import pytest

import amazon_cloud_code_generator.cmd.utils as ut


def test__python_type():
    assert ut.python_type("object") == "dict"
    assert ut.python_type("string") == "str"
    assert ut.python_type("array") == "list"
    assert ut.python_type("list") == "list"
    assert ut.python_type("boolean") == "bool"


options = {
    'ManagedPolicyArns': {
        'description': [
            'A list of Amazon Resource Names (ARNs) of the IAM managed policies that you want to attach to the role.'
        ],
        'type': 'list',
        'uniqueItems': True,
        'insertionOrder': False,
        'elements': 'str',
        'additionalProperties': False
    },
    'TransitionDate': {
        'description': [
            'The date value in ISO 8601 format.',
            'The timezone is always UTC. (YYYY-MM-DDThh:mm:ssZ)'
        ],
        'type': 'str',
        'pattern': '^([0-2]\\d{3})-(0[0-9]|1[0-2])-([0-2]\\d|3[01])T([01]\\d|2[0-4]):([0-5]\\d):([0-6]\\d)((\\.\\d{3})?)Z$'
    }
}


def test__scrub_keys():
    list_of_keys_to_remove = ["additionalProperties", "insertionOrder", "uniqueItems", "pattern", "maxLength", "minLength", "format"]
    options_scrubbed = {
        'ManagedPolicyArns': {
            'description': [
                'A list of Amazon Resource Names (ARNs) of the IAM managed policies that you want to attach to the role.'
            ],
            'type': 'list',
            'elements': 'str'
        },
        'TransitionDate': {
            'description': [
                'The date value in ISO 8601 format.',
                'The timezone is always UTC. (YYYY-MM-DDThh:mm:ssZ)',
            ],
            'type': 'str',
        }
    }
    assert ut.scrub_keys(options, list_of_keys_to_remove) == options_scrubbed
