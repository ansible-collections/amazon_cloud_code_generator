#!/usr/bin/env python3

import argparse
import io
import pathlib
from typing import Dict, List
import ruamel.yaml
import yaml


def _task_to_string(task: Dict) -> str:
    a = io.StringIO()
    _yaml = ruamel.yaml.YAML()
    _yaml.dump([task], a)
    a.seek(0)
    return a.read().rstrip()


def get_nested_tasks(task: Dict, target_dir: str) -> List:
    tasks: List = []
    if "include_tasks" in task:
        tasks += get_tasks(target_dir, play=task["include_tasks"])
    elif "import_tasks" in task:
        tasks += get_tasks(target_dir, play=task["import_tasks"])
    else:
        tasks.append(task)

    return tasks


def get_tasks(target_dir: str, play: str = "main.yml") -> List:
    tasks: List = []
    current_file = target_dir / play

    with open(current_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    for task in data:
        if "include_tasks" in task:
            tasks += get_tasks(target_dir, play=task["include_tasks"])
        elif "import_tasks" in task:
            tasks += get_tasks(target_dir, play=task["import_tasks"])
        elif "block" in task:
            for item in task["block"]:
                tasks += get_nested_tasks(item, target_dir)
        elif "always" in task:
            for item in task["always"]:
                tasks += get_nested_tasks(item, target_dir)
        else:
            tasks.append(task)

    return tasks


def extract(tasks: List, collection_name: str) -> Dict:
    by_modules: Dict = {}

    for item in tasks:
        if "tags" in item and "docs" in item["tags"]:
            item.pop("tags")

            if "ignore_errors" in item:
                item.pop("ignore_errors")

            module_fqcn = None
            for key in list(item.keys()):
                if key.startswith(collection_name):
                    module_fqcn = key
                    break

            if not module_fqcn:
                continue

            if module_fqcn not in by_modules:
                by_modules[module_fqcn] = {
                    "blocks": [],
                }
            by_modules[module_fqcn]["blocks"] += [item]

    return by_modules


def flatten_module_examples(module_examples: List) -> str:
    result: str = ""
    blocks = module_examples["blocks"]
    seen: List = []

    for block in blocks:
        if block in seen:
            continue
        seen.append(block)
        result += "\n" + _task_to_string(block) + "\n"
    return result


def inject(target_dir: str, extracted_examples: List):
    module_dir = target_dir / "plugins" / "modules"
    for module_fqcn in extracted_examples:
        module_name = module_fqcn.split(".")[-1]
        module_path = module_dir / (module_name + ".py")
        if module_path.is_symlink():
            continue

        examples_section_to_inject = flatten_module_examples(
            extracted_examples[module_fqcn]
        )
        new_content = ""
        in_examples_block = False
        for l in module_path.read_text().split("\n"):
            if l == 'EXAMPLES = r"""':
                in_examples_block = True
                new_content += l + "\n" + examples_section_to_inject.lstrip("\n")
            elif in_examples_block and l == '"""':
                in_examples_block = False
                new_content += l + "\n"
            elif in_examples_block:
                continue
            else:
                new_content += l + "\n"
        new_content = new_content.rstrip("\n") + "\n"
        print(f"Updating {module_name}")
        module_path.write_text(new_content)


def main():
    parser = argparse.ArgumentParser(description="Build the amazon.cloud modules.")
    parser.add_argument(
        "--target-dir",
        dest="target_dir",
        type=pathlib.Path,
        default=pathlib.Path("cloud"),
        help="location of the target repository (default: ./cloud)",
    )

    args = parser.parse_args()
    galaxy_file = args.target_dir / "galaxy.yml"
    galaxy = yaml.safe_load(galaxy_file.open())
    collection_name = f"{galaxy['namespace']}.{galaxy['name']}"
    tasks = []
    test_scenarios_dir = args.target_dir / "tests" / "integration" / "targets"
    for scenario_dir in test_scenarios_dir.glob("*"):
        if not scenario_dir.is_dir():
            continue
        task_dir = scenario_dir / "tasks"
        tasks += get_tasks(task_dir)

    extracted_examples = extract(tasks, collection_name)
    inject(args.target_dir, extracted_examples)


if __name__ == "__main__":
    main()
