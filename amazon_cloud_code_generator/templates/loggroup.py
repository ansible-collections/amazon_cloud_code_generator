#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: loggroup
version_added: 1.0.0
short_description: Manage resources using the AWS Cloud API
description:
  - Manage resources using the AWS Cloud API
options:
  role_arn:
    description:
      - The identifier of the resource. Gathers information on all resources by default.
    type: str
  client_token:
    description:
      - The identifier of the resource. Gathers information on all resources by default.
    type: str
  state:
    description:
      - The state operation to perform on the resource.
    choices:
      - create
      - delete
      - update
      - describe
      - list
    type: str
    default: create
  desired_state:
    description:
      - Dictionary of desired resource property states
    type: dict
    suboptions:
      log_group_name:
        description: foo
        type: str
      kms_key_id:
        description: foo
        type: str
      retention_in_days:
        description: foo
        type: int
      tags:
        description: foo
        type: dict
      arn:
        description: foo
        type: str
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

 - name: List a specific Log Group
   loggroup:
     log_group_name: '/aws/lambda/ansible-test-lab'
     state: list
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import json
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.basic import missing_required_lib
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

from ..module_utils.core import CloudControlResource


def main():

    argument_spec = dict(
        role_arn=dict(type='str'),
        log_group_name=dict(type='str', required=False),
        client_token=dict(type='str', no_log=True),
        state=dict(type='str', choices=['create', 'update', 'delete', 'list', 'describe'], default='create'),
        kms_key_id=dict(type='str', required=False),
        retention_in_days=dict(type='int', required=False),
        tags=dict(type='dict', required=False),
        arn=dict(type='str', required=False)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    cloud = CloudControlResource(module)

    type_name = 'AWS::Logs::LogGroup'
    params = dict()
    params['LogGroupName'] = module.params.get('log_group_name')
    params['KmsKeyId'] = module.params.get('kms_key_id')
    params['RetentionInDays'] = module.params.get('retention_in_days')
    params['Tags'] = module.params.get('tags')
    params['Arn'] = module.params.get('arn')

    state = module.params.get('state')

    if state == 'list':
        response = cloud.list_resources(type_name)

    # RETURNED RESPONSE SNIPPET FROM LOGGROUP:
    #
    #     "ResourceDescriptions": [
    #         {
    #             "Identifier": "/aws/ecs/containerinsights/ansible-test-bionic-45551755/performance",
    #             "Properties": "{\"RetentionInDays\":1,\"LogGroupName\":\"/aws/ecs/containerinsights/ansible-test-bionic-45551755/performance\",\"Arn\":\"arn:aws:logs:us-west-2:523895541532:log-group:/aws/ecs/containerinsights/ansible-test-bionic-45551755/performance:*\"}"
    #         },
    #         {
    #             "Identifier": "/aws/ecs/containerinsights/ansible-test-bionic-48310714/performance",
    #             "Properties": "{\"RetentionInDays\":1,\"LogGroupName\":\"/aws/ecs/containerinsights/ansible-test-bionic-48310714/performance\",\"Arn\":\"arn:aws:logs:us-west-2:523895541532:log-group:/aws/ecs/containerinsights/ansible-test-bionic-48310714/performance:*\"}"
    #         },
    #
    # if identifer is not None:
    #     # TODO: this is a temporary hack that doesn't work for all states, fix later
    #     try:
    #         response = [cloud.get_resource(type_name, identifer)['ResourceDescription']]
    #     except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    #         module.fail_json_aws(e, msg="")
    # else:
    #     try:
    #         response = cloud.list_resources(type_name)['ResourceDescriptions']
    #     except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    #         module.fail_json_aws(e, msg="")
    # for resource in response:
    #     # Convert the ResourceModel from a str back to json
    #     resource['ResourceModel'] = json.loads(resource['ResourceModel'])

    # result = [camel_dict_to_snake_dict(resource) for resource in response]

    module.exit_json(resources=response)


if __name__ == '__main__':
    main()
