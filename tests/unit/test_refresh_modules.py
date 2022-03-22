import os
import pytest
import json
from pathlib import Path
from typing import Dict

import amazon_cloud_code_generator.cmd.refresh_modules as rm
import amazon_cloud_code_generator.cmd.generator as g


def resources(filepath):
    current = Path(os.path.dirname(os.path.abspath(__file__)))
    with open(current / filepath) as fp:
        return json.load(fp)


raw_content = resources("fixtures/raw_content.json")
expected_content = resources("fixtures/expected_content.json")


def test__gen_required_if():
    expected_required_if = [
        ['state', 'update', ['log_group_name'], True], ['state', 'delete', ['log_group_name'], True], ['state', 'get', ['log_group_name'], True]
    ]
    schema: Dict[str, rm.Schema] = raw_content
    assert rm.gen_required_if(schema["primaryIdentifier"], schema.get("required")) == expected_required_if


def test__generate_params():
    expected_params = """
params['kms_key_id'] = module.params.get('kms_key_id')
params['log_group_name'] = module.params.get('log_group_name')
params['retention_in_days'] = module.params.get('retention_in_days')
params['tags'] = module.params.get('tags')"""
    schema: Dict[str, rm.Schema] = raw_content
    module = rm.AnsibleModule(schema=schema)
    added_ins = {"module": '1.0.0'}
    documentation = g.generate_documentation(
            module,
            added_ins,
            "",
    )
    assert rm.generate_params(documentation["options"]) == expected_params


def test__format_documentation():
    expected = """r'''
module: logs_log_group
short_description: Create and manage log groups
description: Create and manage log groups (list, create, update, describe, delete).
options:
    kms_key_id:
        description:
        - The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
        type: str
    log_group_name:
        description:
        - The name of the log group.
        - If you dont specify a name, AWS CloudFormation generates a unique ID for
            the log group.
        type: str
    retention_in_days:
        choices:
        - 1
        - 3
        - 5
        - 7
        - 14
        - 30
        - 60
        - 90
        - 120
        - 150
        - 180
        - 365
        - 400
        - 545
        - 731
        - 1827
        - 3653
        description:
        - The number of days to retain the log events in the specified log group.
        - 'Possible values are: C(1), C(3), C(5), C(7), C(14), C(30), C(60), C(90),
            C(120), C(150), C(180), C(365), C(400), C(545), C(731), C(1827), and C(3653).'
        type: int
    state:
        choices:
        - create
        - update
        - delete
        - list
        - describe
        - get
        default: create
        description:
        - Goal state for resouirce.
        - I(state=create) creates the resouce.
        - I(state=update) updates the existing resouce.
        - I(state=delete) ensures an existing instance is deleted.
        - I(state=list) get all the existing resources.
        - I(state=describe) or I(state=get) retrieves information on an existing resource.
        type: str
    tags:
        description:
        - A key-value pair to associate with a resource.
        elements: dict
        suboptions:
            key:
                description:
                - The key name of the tag.
                - You can specify a value that is 1 to 128 Unicode characters in length
                    and cannot be prefixed with aws:.
                - 'You can use any of the following characters: the set of Unicode
                    letters, digits, whitespace, _, ., :, /, =, +, - and @.'
                required: true
                type: str
            value:
                description:
                - The value for the tag.
                - You can specify a value that is 0 to 256 Unicode characters in length.
                - 'You can use any of the following characters: the set of Unicode
                    letters, digits, whitespace, _, ., :, /, =, +, - and @.'
                required: true
                type: str
        type: list
    wait:
        default: false
        description:
        - Wait for operation to complete before returning.
        type: bool
    wait_timeout:
        default: 320
        description:
        - How many seconds to wait for an operation to complete before timing out.
        type: int
author: Ansible Cloud Team (@ansible-collections)
version_added: 1.0.0
requirements: []
'''"""

    schema: Dict[str, rm.Schema] = raw_content
    module = rm.AnsibleModule(schema=schema)
    added_ins = {"module": '1.0.0'}
    documentation = g.generate_documentation(
            module,
            added_ins,
            "1.0.0",
    )

    assert rm.format_documentation(documentation) == expected


def test__generate_argument_spec():
    expected_argument_spec = """
argument_spec['log_group_name'] = {'type': 'str'}
argument_spec['kms_key_id'] = {'type': 'str'}
argument_spec['retention_in_days'] = {'type': 'int', 'choices': [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]}
argument_spec['tags'] = {'type': 'list', 'elements': 'dict', 'suboptions': {'key': {'type': 'str', 'required': True}, 'value': {'type': 'str', 'required': True}}}
argument_spec['state'] = {'type': 'str', 'choices': ['create', 'update', 'delete', 'list', 'describe', 'get'], 'default': 'create'}
argument_spec['wait'] = {'type': 'bool', 'default': False}
argument_spec['wait_timeout'] = {'type': 'int', 'default': 320}"""
    schema: Dict[str, rm.Schema] = raw_content
    module = rm.AnsibleModule(schema=schema)
    added_ins = {"module": '1.0.0'}
    documentation = g.generate_documentation(
            module,
            added_ins,
            "",
    )

    assert rm.generate_argument_spec(documentation["options"]) == expected_argument_spec


def test_AnsibleModule():
    schema: Dict[str, rm.Schema] = raw_content
    module = rm.AnsibleModule(schema=schema)
    assert module.name == "logs_log_group"


def test_AnsibleModuleBase_is_trusted():
    schema: Dict[str, rm.Schema] = raw_content
    module = rm.AnsibleModule(schema=schema)
    assert module.is_trusted()
    module.name = "something_we_dont_trust"
    assert not module.is_trusted()
