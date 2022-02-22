#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import copy
import re
from typing import Iterable, List, Dict

from .utils import (
    python_type, scrub_keys,
    camel_to_snake,
    get_module_from_config,
    _camel_to_snake
)


class Description:
    @classmethod
    def normalize(cls, definitions: Iterable, string: str) -> List[str]:
        with_no_line_break: List[str] = []
        sentences = re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', string)

        for l in sentences:
            if "\n" in l:
                with_no_line_break += l.split("\n")
            else:
                with_no_line_break.append(l)

        with_no_line_break = [cls.clean_up(definitions, i) for i in with_no_line_break]
        
        return with_no_line_break
    

    @classmethod
    def clean_up(cls, definitions: Iterable, my_string: str) -> str:
        values = set()
        keys_to_keep = set(["JavaScript", "EventBridge", "CloudFormation", "CloudWatch", "ACLs", "XMLHttpRequest"])
        values_to_keep = set(["PUT"])
        
        def get_values(a_dict):
            for key, value in a_dict.items():
                if isinstance(value, dict):
                    yield from get_values(value)
                else:
                    if key in ("choices", "enum"):
                        yield value
        
        for value in get_values(definitions):
            values |= set(value)
            
        def rewrite_name(matchobj):
            name = matchobj.group(0)
            if name not in keys_to_keep:
                snake_name = _camel_to_snake(name)
                output = f"I({snake_name})"
                return output
            return name

        def rewrite_value(matchobj):
            name = matchobj.group(0)
            if name in values and name not in values_to_keep:
                output = f"C({name})"
                return output
            return name

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
            lword = re.sub(r"([A-Z]+[A-Za-z]+)+([A-Z][a-z]+)+", rewrite_name, line) 
            lword = re.sub(r'[A-Z_]+[0-9A-Z]+', rewrite_value, lword)
            return lword
                
        my_string = format_string(my_string)
        
        # Find link and replace it with U(link)
        my_string = re.sub(r'(https?://[^\s]+)', rewrite_link, my_string)
        
        # Clean un phrase removing square brackets contained words
        my_string = re.sub(r"[\[].*?[\]]", "", my_string)
        
        # Substituting one or more white space which is at beginning and end of the string with an empty string
        my_string = re.sub(r"^\s+|\s+$", "", my_string)
        
        my_string = re.sub(r"TRUE", "C(True)", my_string)
        
        # Remove quotes
        my_string = my_string.replace('"', '')
        my_string = my_string.replace("'", '')
        
        return my_string


class Documentation:    
    def replace_keys(self, options: Iterable, definitions: Iterable):
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
                                item["description"].extend(result.pop("description"))
                                item["description"] = list(Description.normalize(self.definitions, item["description"]))
                            else:
                                item["description"] += result.pop("description")
                                item["description"] = list(Description.normalize(self.definitions, item["description"]))
                                
                        item.update(result)
                        options[key] = item
                
                
                self.replace_keys(options[key], definitions)
            
            elif isinstance(item, str): 
                if key == "type":
                    options[key] = python_type(options[key])
                if key == "description":
                    options[key] = list(Description.normalize(self.definitions, options[key]))
                if key == "const":
                    options["default"] = options.pop(key)
    
    def ensure_required(self, a_dict: Iterable):
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
                
            self.ensure_required(a_dict[k])
                        
    def preprocess(self) -> Iterable:
        list_of_keys_to_remove = ["additionalProperties", "insertionOrder", "uniqueItems", "pattern", "examples", "maxLength", "minLength", "format"]
        self.replace_keys(self.options, self.definitions)
        self.ensure_required(self.options)
        
        if self.required:
            for r in self.required:
                self.options[r]["required"] = True
        
        return camel_to_snake(scrub_keys(self.options, list_of_keys_to_remove))

def generate_documentation(module, added_ins: Dict, next_version: str) -> Iterable:
    """Format and generate the AnsibleModule documentation"""

    module_name = module.name
    definitions = module.schema.get("definitions")
    options = module.schema.get("properties")
    required = module.schema.get("required")
    documentation: Iterable = {
        "module": module_name,
        "author": "Ansible Cloud Team (@ansible-collections)",
        "description": [],
        "short_description": [],
        "options": {},
        "requirements": [],
        "version_added": added_ins["module"] or next_version,
    }
    
    docs = Documentation()
    docs.options = options
    docs.definitions = definitions
    docs.required = required
    documentation["options"] = docs.preprocess()
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
