#!/usr/bin/env python3

import os
import re
import argparse
from functools import lru_cache
import pathlib
import subprocess
from xml.dom.minidom import Document
import pkg_resources
from pbr.version import VersionInfo
import baron
import redbaron
import yaml
import jinja2
import json

import boto3


from generator import python_type
from generator import generate_documentation
from generator import get_module_from_config
from generator import resources_test
from generator import CloudFormationWrapper
from generator import MODULE_NAME_MAPPING

def run_git(git_dir, *args):
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
def file_by_tag(git_dir):
    tags = run_git(git_dir, "tag")

    files_by_tag = {}
    for tag in tags:
        files_by_tag[tag] = run_git(git_dir, "ls-tree", "-r", "--name-only", tag)

    return files_by_tag


def get_module_added_ins(module_name, git_dir):
    added_ins = {"module": None, "options": {}}
    module = f"plugins/modules/{module_name}.py"

    for tag, files in file_by_tag(git_dir).items():
        print("tag, files", tag, files)
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


def _indent(text_block, indent=0):
    result = ""
    for l in text_block.split("\n"):
        result += " " * indent
        result += l
        result += "\n"
    return result


def gen_arguments_py(parameters, list_index=None):
    result = ""
    for parameter in parameters:
        name = parameter["name"]
        values = []

        if parameter.get("required"):
            values.append("'required': True")

        aliases = parameter.get("aliases")
        if aliases:
            values.append(f"'aliases': {aliases}")

        _type = python_type(parameter["type"])
        values.append(f"'type': '{_type}'")
        if "enum" in parameter:
            choices = ", ".join([f"'{i}'" for i in sorted(parameter["enum"])])
            values.append(f"'choices': [{choices}]")
        if python_type(parameter["type"]) == "list":
            _elements = python_type(parameter["elements"])
            values.append(f"'elements': '{_elements}'")

        elif "default" in parameter:
            default = parameter["default"]
            values.append(f"'default': '{default}'")

        result += f"\nargument_spec['{name}'] = "
        result += "{" + ", ".join(values) + "}"
    return result


class Resource:
    def __init__(self, name):
        self.name = name
        self.operations = {}
        self.summary = {}


class AnsibleModuleBase:
    def __init__(self, name, description, definitions):
        self.description = description
        self.definitions = definitions
        self.name = name
        self.default_operationIds = None

    def description(self):
        prefered_operationId = ["get", "list", "create", "update", "delete"]
        for operationId in prefered_operationId:
            if operationId not in self.default_operationIds:
                continue
            if operationId in self.resource.summary:
                return self.resource.summary[operationId].split("\n")[0]

        for operationId in sorted(self.default_operationIds):
            if operationId in self.resource.summary:
                return self.resource.summary[operationId].split("\n")[0]

        print(f"generic description: {self.name}")
        return f"Handle resource of type {self.name}"
    
    def get_path(self):
        return list(self.resource.operations.values())[0][1]

    def is_trusted(self):
        if get_module_from_config(self.name) is False:
            print(f"- do not build: {self.name}")
        else:
            return True
    
    def list_index(self):
        for i in ["get", "update", "delete"]:
            if i not in self.resource.operations:
                continue
            path = self.resource.operations[i][1]
            break
        else:
            return

        m = re.search(r"{([-\w]+)}$", path)
        if m:
            return m.group(1)
    
    def write_module(self, target_dir, content):
        module_dir = target_dir / "plugins" / "modules"
        module_dir.mkdir(parents=True, exist_ok=True)
        module_py_file = module_dir / "{name}.py".format(name=self.name)
        module_py_file.write_text(content)
    
    def renderer(self, target_dir, next_version):

        added_ins = get_module_added_ins(self.name, git_dir=target_dir / ".git")
        #arguments = gen_arguments_py(self.parameters(), self.list_index())
        documentation = generate_documentation(
            self.name,
            self.description,
            pretty(self.definitions.definitions),
            added_ins,
            next_version,
        )

        #required_if = self.gen_required_if(self.parameters())

        content = jinja2_renderer(
            self.template_file,
            #arguments=_indent(arguments, 4),
            documentation=documentation,
            #list_index=self.list_index(),
            name=self.name,
            #required_if=required_if,
        )

        #print("CONTENT", content)

        self.write_module(target_dir, content)


class AnsibleModule(AnsibleModuleBase):
    template_file = "default_module.j2"

    def __init__(self, name, description, definitions):
        super().__init__(name, description, definitions)
        # TODO: We can probably do better
        self.default_operationIds = []
    
    #def parameters(self):
    #    return [i for i in list(super().parameters()) if i["name"] != "state"]



class Definitions:
    def __init__(self, type_name, definitions):
        self.type_name = type_name
        self.definitions = definitions
    
    @property
    def type_name(self):
        return self._type_name
    
    @type_name.setter
    def type_name(self, a):
        self._type_name = a
       
    @property
    def definitions(self):
        return self._definitions
    
    @definitions.setter
    def definitions(self, a):
        self._definitions = a


class Path:
    def __init__(self, path, value):
        super().__init__()
        self.path = path
        self.operations = {}
        self.verb = {}
        self.value = value

    def summary(self, verb):
        return self.value[verb]["summary"]

    def is_tech_preview(self):
        for verb in self.value.keys():
            if "Technology Preview" in self.summary(verb):
                return True
        return False

def pretty(d, indent=10, result=""):
    for key, value in d.items():
        result += " " * indent + str(key)
        if isinstance(value, dict):
            result = pretty(value, indent + 2, result + "\n")
        else:
            result += ": " + str(value) + "\n"
    return result


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
        "--next-version", type=str, default="TODO", help="the next major version",
    )
    args = parser.parse_args()

    module_list = []
    
    for type_name in resources_test:
        print("Generating modules")
        cloudformation = CloudFormationWrapper(boto3.client('cloudformation'))
        raw_content = cloudformation.generate_docs(
            type_name
        )
        
        for type_name in resources_test:
            json_content = json.loads(raw_content)
            type_name = json_content.get("typeName")
            description = json_content.get("description")
            module_name = MODULE_NAME_MAPPING[type_name]
            definitions = Definitions(type_name, json_content.get("definitions"))

            module = AnsibleModule(module_name, description=description, definitions=definitions)

            if module.is_trusted():
                module.renderer(
                    target_dir=args.target_dir, next_version=args.next_version
                )
                module_list.append(module.name)
            module_list.append(module_name)


        # for resource in resources.values():
        #     if "list" in resource.operations:
        #         module = AnsibleInfoListOnlyModule(
        #             resource, definitions=swagger_file.definitions
        #         )
        #         if module.is_trusted() and len(module.default_operationIds) > 0:
        #             module.renderer(
        #                 target_dir=args.target_dir, next_version=args.next_version
        #             )
        #             module_list.append(module.name)
        #     elif "get" in resource.operations:
        #         module = AnsibleInfoNoListModule(
        #             resource, definitions=swagger_file.definitions
        #         )
        #         if module.is_trusted() and len(module.default_operationIds) > 0:
        #             module.renderer(
        #                 target_dir=args.target_dir, next_version=args.next_version
        #             )
        #             module_list.append(module.name)

        #     module = AnsibleModule(resource, definitions=swagger_file.definitions)

        #     if module.is_trusted() and len(module.default_operationIds) > 0:
        #         module.renderer(
        #             target_dir=args.target_dir, next_version=args.next_version
        #         )
        #         module_list.append(module.name)

    files = [f"plugins/modules/{module}.py" for module in module_list]
    files += ["plugins/module_utils/core.py"]
    ignore_dir = args.target_dir / "tests" / "sanity"
    ignore_dir.mkdir(parents=True, exist_ok=True)
    # ignore_content = (
    #     "plugins/modules/vcenter_vm_guest_customization.py pep8!skip\n"  # E501: line too long (189 > 160 characters)
    #     "plugins/modules/appliance_infraprofile_configs.py pep8!skip\n"  # E501: line too long (302 > 160 characters)
    # )

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
                "validate-modules:missing-main-call",  # there is an async main()
            ]
        elif version == "2.12":
            # https://docs.python.org/3.10/library/asyncio-eventloop.html#asyncio.get_event_loop
            # with py3.10, get_event_loop() raises a deprecation warning. We will switch to asyncio.run()
            # when we will drop py3.6 support.
            skip_list += [
                "import-3.10!skip",
            ]

        #per_version_ignore_content = ignore_content
        for f in files:
            for test in skip_list:
                # Sanity test 'validate-modules' does not test path 'plugins/module_utils/vmware_rest.py'
                if version in ["2.9", "2.10", "2.11"]:
                    if f == "plugins/module_utils/core.py":
                        if test.startswith("validate-modules:"):
                            continue
                #per_version_ignore_content += f"{f} {test}\n"

        #ignore_file = ignore_dir / f"ignore-{version}.txt"
        #ignore_file.write_text(per_version_ignore_content)

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