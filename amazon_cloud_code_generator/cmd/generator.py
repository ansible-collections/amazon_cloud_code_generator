#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import copy
import re
from typing import List, Dict
import yaml
import pkg_resources

from .resources import RESOURCES, MODULE_NAME_MAPPING


def python_type(value: str) -> str:
    TYPE_MAPPING = {
        "array": "list",
        "boolean": "bool",
        "integer": "int",
        "object": "dict",
        "string": "str",
    }
    return TYPE_MAPPING.get(value, value)


def scrub_keys(a_dict: Dict, list_of_keys_to_remove) -> Dict:
    """Filter a_dict by removing unwanted key: values listed in list_of_keys_to_remove"""   
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


class Description:
    @classmethod
    def normalize(cls, string: str) -> List[str]:
        with_no_line_break = []
        sentences = re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', string)

        for l in sentences:
            if "\n" in l:
                with_no_line_break += l.split("\n")
            else:
                with_no_line_break.append(l)

        with_no_line_break = [cls.clean_up(i) for i in with_no_line_break]

        return with_no_line_break
    
    @classmethod
    def to_snake(cls, camel_case):
        return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_case).lower()

    @classmethod
    def clean_up(cls, my_string: str) -> str:
        def rewrite_name(matchobj):
            name = matchobj.group(0)
            snake_name = cls.to_snake(name)
            output = f"I({snake_name})"
            return output

        def rewrite_value(matchobj):
            name = matchobj.group(0)
            output = f"C({name})"
            return output

        def rewrite_link(matchobj):
            """Find link and replace it with U(link)"""
            name = matchobj.group(0)
            output = f"U({name})"
            return output
        
        def format_string(line):
            """
            Find CamelCase words (likely to be parameter names, some rewite I(to_snake)
            Find uppercase words (likely to be values like EXAMPLE or EXAMPLE_EXAMPLE and replace with C(to lower)
            """
            words = re.split(r'(https?://[^\s]+)', line)
            
            result = []
            for word in words:
                lword = re.sub(r"(?:[A-Z])(?:\S?)+(?:[A-Z])(?:[a-z])+", rewrite_name, word)
                lword = re.sub(r'[A-Z_]+[0-9A-Z]+', rewrite_value, lword)
                result.append(lword)
            return " ".join(result)
                
        my_string = format_string(my_string)
        
        # Find link and replace it with U(link)
        my_string = re.sub(r'(https?://[^\s]+)', rewrite_link, my_string)
        
        # Clean un phrase removing square brackets contained words
        my_string = re.sub(r"[\[].*?[\]]", "", my_string)
        
        return my_string


class Documentation:
    @classmethod
    def replace_keys(cls, options, definitions):
        """Sanitize module's options and replace $ref with the correspoding parameters"""
        dict_copy = copy.copy(options)
        for key in dict_copy.keys():
            item = options[key]

            if isinstance(item, list):            
                if key == "enum":
                    options["choices"] = sorted(options.pop(key))
            elif isinstance(item, dict):
                if key == "properties":
                    options["suboptions"] = options.pop(key)
                    key = "suboptions"
                
                if  "$ref" in item:
                    lookup_param = item['$ref'].split('/')[-1].strip()
                    if definitions.get(lookup_param):
                        result = definitions[lookup_param]
                        item.pop("$ref")
                        if item.get("description") and result.get("description"):
                            if isinstance(item["description"], list):
                                item["description"].extend([result.pop("description")])
                            else:
                                item["description"] += result.pop("description")
                        item.update(result)
                        options[key] = item
                
                cls.replace_keys(options[key], definitions)
            
            elif isinstance(item, str): 
                if key == "type":
                    options[key] = python_type(options[key])
                if key == "description":
                    options[key] = list(Description.normalize(options[key]))
                if key == "const":
                    options["default"] = options.pop(key)
    
    @classmethod
    def ensure_required(cls, a_dict):
        """Add required=True for specific parameters"""
        a_dict_copy = copy.copy(a_dict)

        if not isinstance(a_dict, dict):
            return a_dict
        
        for k, v in a_dict_copy.items():
            if isinstance(v, dict):
                if "items" in a_dict[k]:
                    if a_dict[k]["items"].get("type"):
                        a_dict[k]["elements"] = python_type(a_dict_copy[k]["items"].pop("type"))
                    a_dict[k] = dict(a_dict_copy[k], **a_dict[k].pop("items"))
                    v = a_dict[k]

                if "required" in v and isinstance(v["required"], list):
                    for r in v["required"]:
                        a_dict[k]["suboptions"][r]["required"] = True
                    a_dict[k].pop("required")
            cls.ensure_required(a_dict[k])
    
    @classmethod
    def preprocess(cls, options, definitions):
        cls.replace_keys(options, definitions)
        cls.ensure_required(options)

        list_of_keys_to_remove = ["additionalProperties", "insertionOrder", "uniqueItems", "pattern", "examples", "maxLength", "minLength", "format"]
        
        return camel_to_snake(scrub_keys(options, list_of_keys_to_remove))


def generate_documentation(module, added_ins: Dict, next_version: str) -> Dict:
    """Format and generate the AnsibleModule documentation"""

    module_name = module.name 
    definitions = module.definitions.definitions
    options = module.options
    documentation = {
        "module": module_name,
        "author": "Ansible Cloud Team (@ansible-collections)",
        "description": [],
        "short_description": [],
        "options": options,
        "requirements": [],
        "version_added": added_ins["module"] or next_version,
    }

    Documentation.preprocess(documentation['options'], definitions)

    documentation["options"].update(
        {
            "wait": {
                "description": ["Wait for operation to complete before returning."],
                "type": "bool",
                "default": False,
            },
            "wait_timeout": {
                "description": ["How many seconds to wait for an operation to complete before timing out."],
                "type": "int",
                "default": 320,
            },
        }
    )

    module_from_config = get_module_from_config(module_name)
    if module_from_config and "documentation" in module_from_config:
        for k, v in module_from_config["documentation"].items():
            documentation[k] = v

    return documentation


class CloudFormationWrapper:
    """Encapsulates Amazon CloudFormation operations."""
    def __init__(self, client):
        """
        :param client: A Boto3 CloudFormation client
        """
        self.client = client
    
    def generate_docs(self, type_name: str):
        """
        Equivalent to
        aws cloudformation describe-type \
            --type-name My::Logs::LogGroup \
            --type RESOURCE
        """
        # TODO: include version
        response = self.client.describe_type(Type='RESOURCE', TypeName=type_name)

        return response.get('Schema')
