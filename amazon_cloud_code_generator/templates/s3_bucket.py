#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from cmath import log
from dataclasses import replace

__metaclass__ = type

DOCUMENTATION = '''
---
module: s3_bucket
version_added: 3.0.0
short_description: Get info (List) about resources using the AWS Cloud API
description:
  - Get info (List) resources using the AWS Cloud API
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
  accelerate_configuration:
    type: str
  access_control:
    type: str
  analytics_configurations:
    type: str
  bucket_encryption:
    type: str
  bucket_name:
    type: str
  cors_configuration:
    type: str
  intelligent_tiering_configurations:
    type: str
  inventory_configurations:
    type: str
  lifecycle_configuration:
    type: str
  logging_configuration:
    type: str
  metrics_configurations:
    type: str
  notification_configuration:
    type: str
  object_lock_configuration:
    type: str
  object_lock_enabled:
    type: str
  ownership_controls:
    type: str
  public_access_block_configuration:
    type: str
  replication_configuration:
    type: str
  tags:
    type: str
  versioning_configuration:
    type: str
  website_configuration:
    type: str
  arn:
    type: str
  domain_name:
    type: str
  dual_stack_domain_name:
    type: str
  regional_domain_name:
    type: str
  website_url:
    type: str

author:
    - Jill Rouleau (@jillr)
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

  - name: Create bucket
    amazon.cloud.s3_bucket:
      state: create
      bucket_name: '{{ bucket_name }}'

  - name: List all buckets
    amazon.cloud.s3_bucket:
      state: list

'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import json
from ansible_collections.amazon.aws.plugins.module_utils.core import \
    AnsibleAWSModule
from ansible_collections.amazon.cloud.plugins.module_utils.core import CloudControlResource
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, snake_dict_to_camel_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


def format_list(response):
    result = list()
    identifier = response.get('ResourceDescription', {}).get('Identifier', None)

    # Convert the Resource Properties from a str back to json
    properties = response.get('ResourceDescription', {}).get('Properties', {})
    properties = json.loads(properties)
    
    bucket = dict()
    bucket['Identifier'] = identifier
    bucket['properties'] = properties
    result.append(bucket)
    
    result = [camel_dict_to_snake_dict(res) for res in result]

    return result


@AWSRetry.jittered_backoff(retries=10)
def _get_resource(client, **params): #  There's no paginator available at the moment
    try:
        paginator = client.get_paginator('get_resource')
        return paginator.paginate(**params).build_full_result()
    except is_boto3_error_code('ResourceNotFoundException'):
        return {}

def diff_dict(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    shared_deltas = {o: (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
    added_keys = d2_keys - d1_keys
    added_deltas = {o: (None, d2[o]) for o in added_keys}
    deltas = {**shared_deltas, **added_deltas}
    return parse_deltas(deltas)


def parse_deltas(deltas: dict):
    res = {}
    for k, v in deltas.items():
        if isinstance(v[0], dict):
            tmp = diff_dict(v[0], v[1])
            if tmp:
                res[k] = tmp
        else:
            res[k] = v[1]
    return res

def main():
    argument_spec = dict(
        role_arn=dict(type='str'),
        client_token=dict(type='str', no_log=True),
        state=dict(type='str',
                   choices=['create', 'update', 'delete', 'list', 'describe'],
                   default='create'),
        accelerate_configuration=dict(type='str', required=False),
        access_control=dict(type='str', required=False),
        analytics_configurations=dict(type='str', required=False),
        bucket_encryption=dict(type='str', required=False),
        bucket_name=dict(type='str', required=False),
        cors_configuration=dict(type='str', required=False),
        intelligent_tiering_configurations=dict(type='str', required=False),
        inventory_configurations=dict(type='str', required=False),
        lifecycle_configuration=dict(type='str', required=False),
        logging_configuration=dict(type='str', required=False),
        metrics_configurations=dict(type='str', required=False),
        notification_configuration=dict(type='str', required=False),
        object_lock_configuration=dict(type='str', required=False),
        object_lock_enabled=dict(type='str', required=False),
        ownership_controls=dict(type='str', required=False),
        public_access_block_configuration=dict(type='dict', required=False),
        replication_configuration=dict(type='str', required=False),
        tags=dict(type='str', required=False),
        versioning_configuration=dict(type='str', required=False),
        website_configuration=dict(type='str', required=False),
        arn=dict(type='str', required=False),
        domain_name=dict(type='str', required=False),
        dual_stack_domain_name=dict(type='str', required=False),
        regional_domain_name=dict(type='str', required=False),
        website_url=dict(type='str', required=False),        
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=False)
    cloud = CloudControlResource(module)

    type_name = 'AWS::S3::Bucket'
    params = dict()

    params['AccelerateConfiguration'] = module.params.get(
        'accelerate_configuration')
    params['AccessControl'] = module.params.get('access_control')
    params['AnalyticsConfigurations'] = module.params.get(
        'analytics_configurations')
    params['BucketEncryption'] = module.params.get('bucket_encryption')
    params['BucketName'] = module.params.get('bucket_name')
    params['CorsConfiguration'] = module.params.get('cors_configuration')
    params['IntelligentTieringConfigurations'] = module.params.get(
        'intelligent_tiering_configurations')
    params['InventoryConfigurations'] = module.params.get(
        'inventory_configurations')
    params['LifecycleConfiguration'] = module.params.get(
        'lifecycle_configuration')
    params['LoggingConfiguration'] = module.params.get('logging_configuration')
    params['MetricsConfigurations'] = module.params.get(
        'metrics_configurations')
    params['NotificationConfiguration'] = module.params.get(
        'notification_configuration')
    params['ObjectLockConfiguration'] = module.params.get(
        'object_lock_configuration')
    params['ObjectLockEnabled'] = module.params.get('object_lock_enabled')
    params['OwnershipControls'] = module.params.get('ownership_controls')

    if module.params.get('public_access_block_configuration'):  # BlockPublicAcls, BlockPublicPolicy, IgnorePublicAcls, RestrictPublicBuckets, 
        params['PublicAccessBlockConfiguration'] = snake_dict_to_camel_dict(module.params.get('public_access_block_configuration'), capitalize_first=True)
  
    params['ReplicationConfiguration'] = module.params.get(
        'replication_configuration')
    params['Tags'] = module.params.get('tags')
    params['VersioningConfiguration'] = module.params.get(
        'versioning_configuration')
    params['WebsiteConfiguration'] = module.params.get('website_configuration')
    params['Arn'] = module.params.get('arn')
    params['DomainName'] = module.params.get('domain_name')
    params['DualStackDomainName'] = module.params.get('dual_stack_domain_name')
    params['RegionalDomainName'] = module.params.get('regional_domain_name')
    params['WebsiteURL'] = module.params.get('website_url')

    state = module.params.get('state')
    changed = False
    result = []

    # The DesiredState we pass to AWS must be a JSONArray of non-null values
    params_to_set = {k: v for k, v in params.items() if v is not None}
    desired_state = json.dumps(params_to_set)

    if state == 'list':
        response = cloud.list_resources(type_name)
        changed = False

    # RETURNED RESPONSE SNIPPET FROM S3_BUCKET
    #
    #     "ResourceDescriptions": [
    # {
    #     "Identifier": "ansible-test-jillr",
    #     "Properties": "{\"BucketName\":\"ansible-test-jillr\"}"
    # }
    # ]
    #

    if state == 'create':  # ConcurrentOperationException if try to create when previously tried to delete, add a waiter
        """
        {'ProgressEvent': {'EventTime': datetime.datetime(2022, 1, 6, 16, 14, 55, 315000, tzinfo=tzlocal()), 'Identifier': 'testdsbugvduskxcb', 'Operation': 'CREATE', 'OperationStatus': 'IN_PROGRESS', 'RequestToken': '0d4f4fb6-c360-4421-ac6c-f1a8cef71449', 'TypeName': 'AWS::S3::Bucket'}, 'ResponseMetadata': {'HTTPHeaders': {'content-length': '217', 'content-type': 'application/x-amz-json-1.0', 'date': 'Thu, 06 Jan 2022 23:14:55 GMT', 'x-amzn-requestid': 'fd6707d7-6301-49af-8272-d642f3d8c90c'}, 'HTTPStatusCode': 200, 'RequestId': 'fd6707d7-6301-49af-8272-d642f3d8c90c', 'RetryAttempts': 0}}
        """
        identifier = params['BucketName']
        try:
            response = cloud.client.get_resource(TypeName=type_name, Identifier=identifier)
        except cloud.client.exceptions.ResourceNotFoundException:
            try:
                response = cloud.create_resource(type_name, desired_state)
                cloud.client.get_waiter('resource_request_success').wait(RequestToken=response['ProgressEvent']['RequestToken'])
            except botocore.exceptions.WaiterError as e:
                module.fail_json_aws(e, msg='An error occurred waiting for the resource request to become successful')
            changed = True
            #response = cloud.client.get_resource(TypeName=type_name, Identifier=identifier)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="")
        
        result = response
        #result = format_list(response)
            

    if state == 'update':
      # Get information about the current state of the specified resource.
      identifier = params['BucketName']
      try:
          response = cloud.client.get_resource(TypeName=type_name, Identifier=identifier)
      except cloud.client.exceptions.ResourceNotFoundException:
          module.exit_json(changed=changed, resources=result)
      except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
          module.fail_json_aws(e, msg="")
      
      properties = response.get('ResourceDescription', {}).get('Properties', {})
      properties = json.loads(properties)
      
      to_be_updated = diff_dict(properties, params_to_set)
      
      def format_patch(data):
          params = []
          for key in data.keys():
              result = {"op": "replace", "path": key, "value": data[key]}
              params.append(result)
          return json.dumps(params)

      if to_be_updated:
          try:
              response = cloud.update_resource(type_name, identifier, format_patch(to_be_updated))
              cloud.client.get_waiter('resource_request_success').wait(RequestToken=response['ProgressEvent']['RequestToken'])
          except botocore.exceptions.WaiterError as e:
              module.fail_json_aws(e, msg='An error occurred waiting for the resource request to become successful')
          changed = True
          result = response
          module.exit_json(changed=changed, resources=result)
      
    if state == 'delete':
      # Get information about the current state of the specified resource.
      identifier = params['BucketName']
      try:
          response = cloud.client.get_resource(TypeName=type_name, Identifier=identifier)
      except cloud.client.exceptions.ResourceNotFoundException:
          module.exit_json(changed=changed, resources=result)

      try:
          response = cloud.delete_resource(type_name, identifier)
          cloud.client.get_waiter('resource_request_success').wait(RequestToken=response['ProgressEvent']['RequestToken'])
      except is_boto3_error_code("NotFound"):
          changed = True
          result = response
      except botocore.exceptions.WaiterError as e:
          module.fail_json_aws(e, msg='An error occurred waiting for the resource request to become successful')
      
      #result = format_list(response)

    # result = [camel_dict_to_snake_dict(result) for resource in response]

    module.exit_json(changed=changed, resources=result)


if __name__ == '__main__':
    main()
