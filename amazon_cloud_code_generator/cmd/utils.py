#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import copy
import re
import yaml
import pkg_resources
from typing import Dict, List


def python_type(value) -> str:
    TYPE_MAPPING = {
        "array": "list",
        "boolean": "bool",
        "integer": "int",
        "object": "dict",
        "string": "str",
    }
    if isinstance(value, list):
        return TYPE_MAPPING.get(value[0], value)
    return TYPE_MAPPING.get(value, value)


# def scrub_keys(a_dict: Dict, list_of_keys_to_remove: List) -> Dict:
#     """Filter a_dict by removing unwanted key: values listed in list_of_keys_to_remove"""
#     a_dict_copy = copy.deepcopy(a_dict)
#     for key in list_of_keys_to_remove:
#         a_dict_copy.pop(key, None)
    
#     return a_dict_copy


def scrub_keys(a_dict: Dict, list_of_keys_to_remove: List) -> Dict:
    if not isinstance(a_dict, dict):
        return a_dict
    return {k: v for k, v in ((k, scrub_keys(v, list_of_keys_to_remove)) for k, v in a_dict.items()) if k not in list_of_keys_to_remove}


def _camel_to_snake(name: str, reversible: bool=False) -> str:

    def prepend_underscore_and_lower(m):
        return '_' + m.group(0).lower()

    if reversible:
        upper_pattern = r'[A-Z]'
    else:
        # Cope with pluralized abbreviations such as TargetGroupARNs
        # that would otherwise be rendered target_group_ar_ns
        upper_pattern = r'[A-Z]{3,}s$'

    s1 = re.sub(upper_pattern, prepend_underscore_and_lower, name)
    # Handle when there was nothing before the plural_pattern
    if s1.startswith("_") and not name.startswith("_"):
        s1 = s1[1:]
    if reversible:
        return s1

    # Remainder of solution seems to be https://stackoverflow.com/a/1176023
    first_cap_pattern = r'(.)([A-Z][a-z]+)'
    all_cap_pattern = r'([a-z0-9])([A-Z]+)'
    s2 = re.sub(first_cap_pattern, r'\1_\2', s1)
    return re.sub(all_cap_pattern, r'\1_\2', s2).lower()


def camel_to_snake(a_dict: Dict) -> Dict:
    b_dict = {}
    for k in a_dict.keys():
        if isinstance(a_dict[k], dict):
            b_dict[_camel_to_snake(k)] = camel_to_snake(a_dict[k])
        else:
            b_dict[_camel_to_snake(k)] = a_dict[k]
    return b_dict


def get_module_from_config(module: str):
    raw_content = pkg_resources.resource_string(
       "amazon_cloud_code_generator", "config/modules.yaml"
    )
    for i in yaml.safe_load(raw_content):
        if module in i:
            return i[module]
    return False

