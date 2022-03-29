#!/usr/bin/env python3


import argparse
from functools import lru_cache
import pathlib
import subprocess
import pkg_resources
from pbr.version import VersionInfo
import baron
import redbaron
import yaml
import jinja2
import json
import traceback

BOTO3_IMP_ERR = None
try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    BOTO3_IMP_ERR = traceback.format_exc()
    HAS_BOTO3 = False

from typing import Dict, Iterable, List, Optional, TypedDict

from .resources import RESOURCES
from .generator import CloudFormationWrapper
from .generator import generate_documentation
from .utils import get_module_from_config
from .utils import camel_to_snake
from .utils import scrub_keys


def run_git(git_dir: str, *args):
    cmd = [
        "git",
        "--git-dir",
        git_dir,
    ]
    for arg in args:
        cmd.append(arg)
    r = subprocess.run(cmd, text=True, capture_output=True)
    return r.stdout.rstrip().split("\n")


@lru_cache(maxsize=None)
def file_by_tag(git_dir: str) -> Dict:
    tags = run_git(git_dir, "tag")

    files_by_tag: Dict = {}
    for tag in tags:
        files_by_tag[tag] = run_git(git_dir, "ls-tree", "-r", "--name-only", tag)

    return files_by_tag


def get_module_added_ins(module_name: str, git_dir: str) -> Dict:
    added_ins = {"module": None, "options": {}}
    module = f"plugins/modules/{module_name}.py"

    for tag, files in file_by_tag(git_dir).items():
        if "rc" in tag:
            continue
        if module in files:
            if not added_ins["module"]:
                added_ins["module"] = tag
            content = "\n".join(
                run_git(
                    git_dir,
                    "cat-file",
                    "--textconv",
                    f"{tag}:{module}",
                )
            )
            try:
                ast_file = redbaron.RedBaron(content)
            except baron.BaronError as e:
                print(f"Failed to parse {tag}:plugins/modules/{module_name}.py. {e}")
                continue
            doc_block = ast_file.find(
                "assignment", target=lambda x: x.dumps() == "DOCUMENTATION"
            )
            if not doc_block or not doc_block.value:
                print(f"Cannot find DOCUMENTATION block for module {module_name}")
            doc_content = yaml.safe_load(doc_block.value.to_python())
            for option in doc_content["options"]:
                if option not in added_ins["options"]:
                    added_ins["options"][option] = tag

    return added_ins


def jinja2_renderer(template_file, **kwargs):
    templateLoader = jinja2.PackageLoader("amazon_cloud_code_generator")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_file)
    return template.render(kwargs)


def indent(text_block: str, indent: int = 0) -> str:
    result: str = ""

    for line in text_block.split("\n"):
        result += " " * indent
        result += line
        result += "\n"
    return result


def generate_params(definitions: Iterable) -> str:
    params: str = ""
    keys = sorted(definitions.keys() - ["wait", "wait_timeout", "state", "purge_tags"])
    for key in keys:
        params += f"\nparams['{key}'] = module.params.get('{key}')"

    return params


def gen_required_if(schema: Dict) -> List:
    primary_idenfifier = schema.get("primaryIdentifier")
    read_only_properties = schema.get("readOnlyProperties")
    required = schema.get("required", [])
    states = ["update", "delete", "get"]
    entries: List = []

    # Require primaryIdentifier only if not marked as a readOnlyProperty and further required properties
    # when state == create
    if primary_idenfifier:
        for pr in primary_idenfifier:
            if pr not in read_only_properties:
                entries.append(["state", "create", [pr, *required], True])

            [entries.append(["state", state, [pr], True]) for state in states]

    return entries


def format_documentation(documentation: Iterable) -> str:
    yaml.Dumper.ignore_aliases = lambda *args: True

    def _sanitize(input):
        if isinstance(input, str):
            return input.replace("':'", ":")
        if isinstance(input, list):
            return [line.replace("':'", ":") for line in input]
        if isinstance(input, dict):
            return {k: _sanitize(v) for k, v in input.items()}
        if isinstance(input, bool):
            return input
        raise TypeError

    keys = [
        "module",
        "short_description",
        "description",
        "options",
        "author",
        "version_added",
        "requirements",
        "seealso",
        "notes",
    ]

    final: str = "r'''\n"
    for i in keys:
        if i not in documentation:
            continue
        if isinstance(documentation[i], str):
            sanitized = _sanitize(documentation[i])
        else:
            sanitized = documentation[i]
        final += yaml.dump({i: sanitized}, indent=4, default_flow_style=False)
    final += "'''"

    return final


def generate_argument_spec(options: Dict) -> str:
    list_of_keys_to_remove = ["description"]
    argument_spec: str = ""

    for key in options.keys():
        argument_spec += f"\nargument_spec['{key}'] = "
        argument_spec += str(scrub_keys(options[key], list_of_keys_to_remove))
    return argument_spec


class Schema(TypedDict):
    """A type for the JSONSchema spec"""

    typeName: str
    description: str
    properties: Dict
    definitions: Optional[Dict]
    required: Optional[List]
    primaryIdentifier: List
    readOnlyProperties: Optional[List]
    createOnlyProperties: Optional[List]
    taggable: Optional[bool]


def generate_schema(raw_content) -> Dict:
    json_content = json.loads(raw_content)
    schema: Dict[str, Schema] = json_content

    for key, value in schema.items():
        if isinstance(value, list):
            schema[key] = [camel_to_snake(p.split("/")[-1].strip()) for p in value]

    return schema


class AnsibleModule:
    template_file = "default_module.j2"

    def __init__(self, schema: Iterable):
        self.schema = schema
        self.name = self.generate_module_name()

    def generate_module_name(self):
        splitted = self.schema.get("typeName").split("::")
        list_to_str = "".join(map(str, splitted[1:]))
        return camel_to_snake(list_to_str)

    def is_trusted(self) -> bool:
        if get_module_from_config(self.name) is False:
            print(f"- do not build: {self.name}")
        else:
            return True

    def write_module(self, target_dir: str, content: str):
        module_dir = target_dir / "plugins" / "modules"
        module_dir.mkdir(parents=True, exist_ok=True)
        module_py_file = module_dir / "{name}.py".format(name=self.name)
        module_py_file.write_text(content)

    def renderer(self, target_dir: str, next_version: str):
        added_ins = get_module_added_ins(self.name, git_dir=target_dir / ".git")
        documentation = generate_documentation(
            self,
            added_ins,
            next_version,
        )
        arguments = generate_argument_spec(documentation["options"])
        documentation_to_string = format_documentation(documentation)
        required_if = gen_required_if(self.schema)
        content = jinja2_renderer(
            self.template_file,
            arguments=indent(arguments, 4),
            documentation=documentation_to_string,
            name=self.name,
            resource_type=f"'{self.schema.get('typeName')}'",
            params=indent(generate_params(documentation["options"]), 4),
            primary_identifier=self.schema["primaryIdentifier"][0],
            required_if=required_if,
            create_only_properties=self.schema.get("createOnlyProperties"),
        )

        self.write_module(target_dir, content)


def main():
    parser = argparse.ArgumentParser(description="Build the amazon.cloud modules.")
    parser.add_argument(
        "--target-dir",
        dest="target_dir",
        type=pathlib.Path,
        default=pathlib.Path("cloud"),
        help="location of the target repository (default: ./cloud)",
    )
    parser.add_argument(
        "--next-version",
        type=str,
        default="TODO",
        help="the next major version",
    )
    args = parser.parse_args()

    module_list = []

    for type_name in RESOURCES:
        print("Generating modules")
        cloudformation = CloudFormationWrapper(boto3.client("cloudformation"))
        raw_content = cloudformation.generate_docs(type_name)
        schema = generate_schema(raw_content)

        module = AnsibleModule(schema=schema)

        if module.is_trusted():
            module.renderer(target_dir=args.target_dir, next_version=args.next_version)
            module_list.append(module.name)

    files = [f"plugins/modules/{module}.py" for module in module_list]
    files += ["plugins/module_utils/core.py"]
    files += ["plugins/module_utils/utils.py"]
    ignore_dir = args.target_dir / "tests" / "sanity"
    ignore_dir.mkdir(parents=True, exist_ok=True)
    ignore_content = "plugins/modules/s3_bucket.py pep8!skip\n"  # E501: line too long (189 > 160 characters)

    for version in ["2.9", "2.10", "2.11", "2.12", "2.13"]:
        skip_list = [
            "compile-2.7!skip",  # Py3.6+
            "compile-3.5!skip",  # Py3.6+
            "import-2.7!skip",  # Py3.6+
            "import-3.5!skip",  # Py3.6+
            "future-import-boilerplate!skip",  # Py2 only
            "metaclass-boilerplate!skip",  # Py2 only
        ]
        # No py26 tests with 2.13 and greater
        if version in ["2.9", "2.10", "2.11", "2.12"]:
            skip_list += [
                "compile-2.6!skip",  # Py3.6+
                "import-2.6!skip",  # Py3.6+
            ]
        if version in ["2.9", "2.10", "2.11"]:
            skip_list += [
                "validate-modules:missing-if-name-main",
            ]

        per_version_ignore_content = ignore_content
        for f in files:
            for test in skip_list:
                # Sanity test 'validate-modules' does not test path 'plugins/module_utils/core.py'
                if version in ["2.9", "2.10", "2.11"]:
                    if f == "plugins/module_utils/core.py":
                        if test.startswith("validate-modules:"):
                            continue
                per_version_ignore_content += f"{f} {test}\n"

        ignore_file = ignore_dir / f"ignore-{version}.txt"
        ignore_file.write_text(per_version_ignore_content)

    info = VersionInfo("amazon_cloud_code_generator")
    dev_md = args.target_dir / "dev.md"
    dev_md.write_text(
        (
            "The modules are autogenerated by:\n"
            "https://github.com/ansible-collections/amazon_cloud_code_generator\n"
            ""
            f"version: {info.version_string()}\n"
        )
    )
    dev_md = args.target_dir / "commit_message"
    dev_md.write_text(
        (
            "bump auto-generated modules\n"
            "\n"
            "The modules are autogenerated by:\n"
            "https://github.com/ansible-collections/amazon_cloud_code_generator\n"
            ""
            f"version: {info.version_string()}\n"
        )
    )

    module_utils_dir = args.target_dir / "plugins" / "module_utils"
    module_utils_dir.mkdir(parents=True, exist_ok=True)
    vmware_rest_dest = module_utils_dir / "core.py"
    vmware_rest_dest.write_bytes(
        pkg_resources.resource_string(
            "amazon_cloud_code_generator", "module_utils/core.py"
        )
    )
    vmware_rest_dest = module_utils_dir / "utils.py"
    vmware_rest_dest.write_bytes(
        pkg_resources.resource_string(
            "amazon_cloud_code_generator", "module_utils/utils.py"
        )
    )


if __name__ == "__main__":
    main()
