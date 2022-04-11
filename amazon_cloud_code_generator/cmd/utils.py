#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import re
import copy
import yaml
import pkg_resources
from typing import Dict, List


def python_type(value) -> str:
    TYPE_MAPPING = {
        "array": "list",
        "boolean": "bool",
        "integer": "int",
        "number": "int",
        "object": "dict",
        "string": "str",
    }
    if isinstance(value, list):
        return TYPE_MAPPING.get(value[0], value)
    return TYPE_MAPPING.get(value, value)


def scrub_keys(a_dict: Dict, list_of_keys_to_remove: List) -> Dict:
    """Filter a_dict by removing unwanted keys: values listed in list_of_keys_to_remove"""
    if not isinstance(a_dict, dict):
        return a_dict
    return {
        k: v
        for k, v in (
            (k, scrub_keys(v, list_of_keys_to_remove)) for k, v in a_dict.items()
        )
        if k not in list_of_keys_to_remove
    }


def ignore_description(a_dict: Dict):
    """
    Filter a_dict by removing description fields.
    Handle when 'description' is a module suboption.
    """
    a_dict_copy = copy.copy(a_dict)
    if not isinstance(a_dict, dict):
        return a_dict

    for k, v in a_dict_copy.items():
        if k == "description":
            if isinstance(v, dict):
                ignore_description(v)
            else:
                a_dict.pop(k)
        ignore_description(v)


def ensure_description(element: Dict, *keys, default: str = "Not Provived."):
    """
    Check if *keys (nested) exists in `element` (dict) and ensure it has the default value.
    """
    if isinstance(element, dict):
        for key, value in element.items():
            if key == "suboptions":
                ensure_description(value, *keys)

            if isinstance(value, dict):
                for akey in keys:
                    if akey not in value:
                        element[key][akey] = [default]
                for k, v in value.items():
                    ensure_description(v, *keys)

    return element


def _camel_to_snake(name: str, reversible: bool = False) -> str:
    def prepend_underscore_and_lower(m):
        return "_" + m.group(0).lower()

    if reversible:
        upper_pattern = r"[A-Z]"
    else:
        # Cope with pluralized abbreviations such as TargetGroupARNs
        # that would otherwise be rendered target_group_ar_ns
        upper_pattern = r"[A-Z]{3,}s$"

    s1 = re.sub(upper_pattern, prepend_underscore_and_lower, name)
    # Handle when there was nothing before the plural_pattern
    if s1.startswith("_") and not name.startswith("_"):
        s1 = s1[1:]
    if reversible:
        return s1

    # Remainder of solution seems to be https://stackoverflow.com/a/1176023
    first_cap_pattern = r"(.)([A-Z][a-z]+)"
    all_cap_pattern = r"([a-z0-9])([A-Z]+)"
    s2 = re.sub(first_cap_pattern, r"\1_\2", s1)
    return re.sub(all_cap_pattern, r"\1_\2", s2).lower()


def camel_to_snake(data: Dict):
    if isinstance(data, str):
        return _camel_to_snake(data)
    elif isinstance(data, list):
        return [_camel_to_snake(r) for r in data]
    elif isinstance(data, dict):
        b_dict: Dict = {}
        for k in data.keys():
            if isinstance(data[k], dict):
                b_dict[_camel_to_snake(k)] = camel_to_snake(data[k])
            else:
                b_dict[_camel_to_snake(k)] = data[k]
        return b_dict


def get_module_from_config(module: str):
    raw_content = pkg_resources.resource_string(
        "amazon_cloud_code_generator", "config/modules.yaml"
    )
    for i in yaml.safe_load(raw_content):
        if module in i:
            return i[module]
    return False
