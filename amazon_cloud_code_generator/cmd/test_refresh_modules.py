import pytest

import amazon_cloud_code_generator.cmd.refresh_modules as rm


schema = {
    "typeName": "AWS::Logs::LogGroup",
    "description": "Resource schema for AWS::Logs::LogGroup",
    "sourceUrl": "https://github.com/aws-cloudformation/aws-cloudformation-resource-providers-logs.git",
    "definitions": {
        "Tag": {
            "description": "A key-value pair to associate with a resource.",
            "type": "object",
            "additionalProperties": false,
            "properties": {
                "Key": {
                    "type": "string",
                    "description": "The key name of the tag. You can specify a value that is 1 to 128 Unicode characters in length and cannot be prefixed with aws:. You can use any of the following characters: the set of Unicode letters, digits, whitespace, _, ., :, /, =, +, - and @.",
                    "minLength": 1,
                    "maxLength": 128
                },
                "Value": {
                    "type": "string",
                    "description": "The value for the tag. You can specify a value that is 0 to 256 Unicode characters in length. You can use any of the following characters: the set of Unicode letters, digits, whitespace, _, ., :, /, =, +, - and @.",
                    "minLength": 0,
                    "maxLength": 256
                }
            },
            "required": [
                "Key",
                "Value"
            ]
        }
    },
    "properties": {
        "LogGroupName": {
            "description": "The name of the log group. If you don't specify a name, AWS CloudFormation generates a unique ID for the log group.",
            "type": "string",
            "minLength": 1,
            "maxLength": 512,
            "pattern": "^[.\\-_/#A-Za-z0-9]{1,512}\\Z"
        },
        "KmsKeyId": {
            "description": "The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.",
            "type": "string",
            "maxLength": 256,
            "pattern": "^arn:[a-z0-9-]+:kms:[a-z0-9-]+:\\d{12}:(key|alias)/.+\\Z"
        },
        "RetentionInDays": {
            "description": "The number of days to retain the log events in the specified log group. Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653.",
            "type": "integer",
            "enum": [
                1,
                3,
                5,
                7,
                14,
                30,
                60,
                90,
                120,
                150,
                180,
                365,
                400,
                545,
                731,
                1827,
                3653
            ]
        },
        "Tags": {
            "description": "An array of key-value pairs to apply to this resource.",
            "type": "array",
            "uniqueItems": true,
            "insertionOrder": false,
            "items": {
                "$ref": "#/definitions/Tag"
            }
        },
        "Arn": {
            "description": "The CloudWatch log group ARN.",
            "type": "string"
        }
    },
    "handlers": {
        "create": {
        "permissions": [
            "logs:DescribeLogGroups",
            "logs:CreateLogGroup",
            "logs:PutRetentionPolicy",
            "logs:TagLogGroup"
        ]
        },
        "read": {
        "permissions": [
            "logs:DescribeLogGroups",
            "logs:ListTagsLogGroup"
        ]
        },
        "update": {
        "permissions": [
            "logs:DescribeLogGroups",
            "logs:AssociateKmsKey",
            "logs:DisassociateKmsKey",
            "logs:PutRetentionPolicy",
            "logs:DeleteRetentionPolicy",
            "logs:TagLogGroup",
            "logs:UntagLogGroup"
        ]
        },
        "delete": {
        "permissions": [
            "logs:DescribeLogGroups",
            "logs:DeleteLogGroup"
        ]
        },
        "list": {
        "permissions": [
            "logs:DescribeLogGroups",
            "logs:ListTagsLogGroup"
        ]
        }
    },
    "createOnlyProperties": [
        "/properties/LogGroupName"
    ],
    "readOnlyProperties": [
        "/properties/Arn"
    ],
    "primaryIdentifier": [
        "/properties/LogGroupName"
    ],
    "additionalProperties": false,
    "taggable": true
}

def test__gen_required_if():
    expected_required_if = []
    assert rm.gen_required_if(schema["primaryIdentifier"], self.schema.get("required")) == expected_required_if


def test__generate_params():
    assert rm.generate_params(options) == expected


def test__format_documentation():
    module = rm.AnsibleModule(schema=schema)
    documentation = generate_documentation(module, "", "")
    assert rm.format_documentation(documentation["options"]) == expected


def test__generate_argument_spec():
    expected_argument_spec = """
argument_spec['log_group_name'] = {'type': 'str'}
argument_spec['kms_key_id'] = {'type': 'str'}
argument_spec['retention_in_days'] = {'type': 'int', 'choices': [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]}
argument_spec['tags'] = {'type': 'list', 'elements': 'dict', 'suboptions': {'key': {'type': 'str', 'required': True}, 'value': {'type': 'str', 'required': True}}}
argument_spec['state'] = {'type': 'str', 'choices': ['create', 'update', 'delete', 'list', 'describe', 'get'], 'default': 'create'}
argument_spec['wait'] = {'type': 'bool', 'default': False}
argument_spec['wait_timeout'] = {'type': 'int', 'default': 320}
    
    """
    module = rm.AnsibleModule(schema=schema)
    documentation = g.generate_documentation(module, "", "")
    assert rm.generate_argument_spec(documentation["options"]) == expected_argument_spec


def test_AnsibleModule():
    module = rm.AnsibleModule(schema=schema)
    assert module.name == "logs_log_group.py"


def test_AnsibleModuleBase_is_trusted():
    module = rm.AnsibleModule(schema=schema)
    assert module.is_trusted()
    module.name = "something_we_dont_trust"
    assert not module.is_trusted()

