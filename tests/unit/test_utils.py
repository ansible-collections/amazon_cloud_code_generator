# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import amazon_cloud_code_generator.cmd.utils as ut

import pytest


def test__python_type():
    assert ut.python_type("object") == "dict"
    assert ut.python_type("string") == "str"
    assert ut.python_type("array") == "list"
    assert ut.python_type("list") == "list"
    assert ut.python_type("boolean") == "bool"


options = {
    "ManagedPolicyArns": {
        "description": [
            "A list of Amazon Resource Names (ARNs) of the IAM managed policies that you want to attach to the role."
        ],
        "type": "list",
        "uniqueItems": True,
        "insertionOrder": False,
        "elements": "str",
        "additionalProperties": False,
    },
    "TransitionDate": {
        "description": [
            "The date value in ISO 8601 format.",
            "The timezone is always UTC. (YYYY-MM-DDThh:mm:ssZ)",
        ],
        "type": "str",
        "pattern": "^([0-2]\\d{3})-(0[0-9]|1[0-2])-([0-2]\\d|3[01])T([01]\\d|2[0-4]):([0-5]\\d):([0-6]\\d)((\\.\\d{3})?)Z$",
    },
}


def test__scrub_keys():
    list_of_keys_to_remove = [
        "additionalProperties",
        "insertionOrder",
        "uniqueItems",
        "pattern",
        "maxLength",
        "minLength",
        "format",
    ]
    options_scrubbed = {
        "ManagedPolicyArns": {
            "description": [
                "A list of Amazon Resource Names (ARNs) of the IAM managed policies that you want to attach to the role."
            ],
            "type": "list",
            "elements": "str",
        },
        "TransitionDate": {
            "description": [
                "The date value in ISO 8601 format.",
                "The timezone is always UTC. (YYYY-MM-DDThh:mm:ssZ)",
            ],
            "type": "str",
        },
    }
    assert ut.scrub_keys(options, list_of_keys_to_remove) == options_scrubbed


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            "",
            "",
        ),
        (
            "foo",
            "foo",
        ),
        (
            "Foo",
            "foo",
        ),
        (
            "FooBar",
            "foo_bar",
        ),
        ("FooBar", "foo_bar"),
        (
            ["Foo", "FooBar", "foo_bar", "FOOBar"],
            ["foo", "foo_bar", "foo_bar", "foo_bar"],
        ),
        (
            {
                "Foo": "Foo",
                "FooBar": "FooBar",
                "foo_bar": "foo_bar",
                "FOOBar": "FOOBar",
            },
            {
                "foo": "Foo",
                "foo_bar": "FooBar",
                "foo_bar": "foo_bar",
                "foo_bar": "FOOBar",
            },
        ),
    ],
)
def test__camel_to_snake(input, expected):
    assert ut.camel_to_snake(input) == expected


def test__ensure_description():
    input = {
        "foo": {"description": ["foo"], "type": "str"},
        "bar": {
            "type": "str",
        },
        "FooBar": {
            "description": ["FooBar"],
            "type": "list",
            "suboptions": {
                "foo_1": {"type": "str"},
                "bar_1": {"type": "dict", "suboptions": {"bar_2": {"type": "str"}}},
            },
        },
    }

    expected = {
        "foo": {"description": ["foo"], "type": "str"},
        "bar": {"type": "str", "description": ["Not Provived."]},
        "FooBar": {
            "description": ["FooBar"],
            "type": "list",
            "suboptions": {
                "foo_1": {"type": "str", "description": ["Not Provived."]},
                "bar_1": {
                    "type": "dict",
                    "suboptions": {
                        "bar_2": {"type": "str", "description": ["Not Provived."]}
                    },
                    "description": ["Not Provived."],
                },
            },
        },
    }
    assert ut.ensure_description(input, "description") == expected
