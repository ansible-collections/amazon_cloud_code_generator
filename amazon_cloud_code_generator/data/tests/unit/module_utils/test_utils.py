# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.amazon.cloud.plugins.module_utils.utils import (
    ansible_dict_to_boto3_tag_list,
    boto3_tag_list_to_ansible_dict,
    diff_dicts,
)


def test__ansible_dict_to_boto3_tag_list():
    tags_dict = {
        "lowerCamel": "lowerCamelValue",
        "UpperCamel": "upperCamelValue",
        "Normal case": "Normal Value",
        "lower case": "lower case value",
    }
    expected = [
        {"Key": "lowerCamel", "Value": "lowerCamelValue"},
        {"Key": "UpperCamel", "Value": "upperCamelValue"},
        {"Key": "Normal case", "Value": "Normal Value"},
        {"Key": "lower case", "Value": "lower case value"},
    ]
    converted_list = ansible_dict_to_boto3_tag_list(tags_dict)
    sorted_converted_list = sorted(converted_list, key=lambda i: (i["Key"]))
    sorted_list = sorted(expected, key=lambda i: (i["Key"]))
    assert sorted_converted_list == sorted_list


def test_boto3_tag_list_to_ansible_dict():
    tag_boto3_list = [
        {"Key": "lowerCamel", "Value": "lowerCamelValue"},
        {"Key": "UpperCamel", "Value": "upperCamelValue"},
        {"Key": "Normal case", "Value": "Normal Value"},
        {"Key": "lower case", "Value": "lower case value"},
    ]
    expected = {
        "lowerCamel": "lowerCamelValue",
        "UpperCamel": "upperCamelValue",
        "Normal case": "Normal Value",
        "lower case": "lower case value",
    }
    converted_dict = boto3_tag_list_to_ansible_dict(tag_boto3_list)
    assert converted_dict == expected


def test_boto3_tag_list_to_ansible_dict_empty():
    # AWS returns [] when there are no tags
    assert boto3_tag_list_to_ansible_dict([]) == {}
    # Minio returns [{}] when there are no tags
    assert boto3_tag_list_to_ansible_dict([{}]) == {}


def test_diff_empty_dicts_no_diff():
    a_dict = {}
    b_dict = {}
    match, diff = diff_dicts(a_dict, b_dict)

    assert match is True
    assert diff == {}


def test_diff_no_diff():
    a_dict = {
        "section1": {"category1": 1, "category2": 2},
        "section2": {
            "category1": 1,
            "category2": 2,
            "category4": {"foo_1": 1, "foo_2": {"bar_1": [1]}},
        },
        "section3": ["elem1", "elem2", "elem3"],
        "section4": ["Foo"],
    }
    match, diff = diff_dicts(a_dict, a_dict)

    assert match is True
    assert diff == {}


def test_diff_no_addition():
    a_dict = {
        "section1": {"category1": 1, "category2": 2},
        "section2": {
            "category1": 1,
            "category2": 2,
            "category4": {"foo_1": 1, "foo_2": {"bar_1": [1]}},
        },
        "section3": ["elem3", "elem1", "elem2"],
        "section4": ["Bar"],
    }
    b_dict = {
        "section1": {"category1": 1, "category2": 2},
        "section2": {
            "category1": 1,
            "category2": 3,
            "category4": {"foo_1": 1, "foo_2": {"bar_1": [1]}},
        },
        "section3": ["elem3", "elem1", "elem2"],
        "section4": ["Foo"],
    }

    match, diff = diff_dicts(a_dict, b_dict)

    assert match is False
    assert diff["before"] == {"section4": ["Bar"], "section2": {"category2": 2}}
    assert diff["after"] == {"section4": ["Foo"], "section2": {"category2": 3}}


def test_diff_with_addition():
    a_dict = {
        "section1": {"category1": 1, "category2": 2},
        "section2": {
            "category1": 1,
            "category2": 2,
            "category4": {"foo_1": 1, "foo_2": {"bar_1": [1]}},
        },
        "section3": ["elem3", "elem1", "elem2"],
        "section4": ["Bar"],
    }
    b_dict = {
        "section1": {"category1": 1, "category2": 2},
        "section2": {
            "category1": 1,
            "category2": 2,
            "category4": {"foo_1": 1, "foo_2": {"bar_1": [1]}},
        },
        "section3": ["elem3", "elem1", "elem2"],
        "section4": ["Foo", "Bar"],
        "section5": ["FooBar"],
    }
    match, diff = diff_dicts(a_dict, b_dict)

    assert match is False
    assert diff["before"] == {"section4": ["Bar"]}
    assert diff["after"] == {"section5": ["FooBar"], "section4": ["Foo", "Bar"]}
