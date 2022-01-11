# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Inspired by https://github.com/ansible-collections/amazon.aws/blob/main/plugins/module_utils/ec2.py
""" The AWS Cloud Control connection plugin
"""

from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type
# pylint: enable=invalid-name

DOCUMENTATION = """
---
connection: aws
short_description: Connect to Amazon Web Services (AWS)
description:
- Connect to Amazon Web Services (AWS)
version_added: 1.0.0
requirements:
  - python >= 3.8
  - boto3 >= 1.15.0
  - botocore >= 1.18.0
options:
  aws_secret_key:
    description:
      - C(AWS secret key). If not set then the value of the C(AWS_SECRET_ACCESS_KEY), C(AWS_SECRET_KEY), or C(EC2_SECRET_KEY) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_secret_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_secret_key, secret_key ]
  aws_access_key:
    description:
      - C(AWS access key). If not set then the value of the C(AWS_ACCESS_KEY_ID), C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_access_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_access_key, access_key ]
  security_token:
    description:
      - C(AWS STS security token). If not set then the value of the C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(security_token) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ aws_security_token, access_token ]
  profile:
    description:
      - Using I(profile) will override I(aws_access_key), I(aws_secret_key) and I(security_token)
        and support for passing them at the same time as I(profile) has been deprecated.
      - I(aws_access_key), I(aws_secret_key) and I(security_token) will be made mutually exclusive with I(profile) after 2022-06-01.
    type: str
    aliases: [ aws_profile ]
notes:
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(AWS_URL) or C(EC2_URL),
    C(AWS_PROFILE) or C(AWS_DEFAULT_PROFILE),
    C(AWS_ACCESS_KEY_ID) or C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY),
    C(AWS_SECRET_ACCESS_KEY) or C(AWS_SECRET_KEY) or C(EC2_SECRET_KEY),
    C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN),
    C(AWS_REGION) or C(EC2_REGION),
    C(AWS_CA_BUNDLE)
  - When no credentials are explicitly provided the AWS SDK (boto3) that
    Ansible uses will fall back to its configuration files (typically
    C(~/.aws/credentials)).
    See U(https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
    for more information.
  - Modules based on the original AWS SDK (boto) may read their default
    configuration from different files.
    See U(https://boto.readthedocs.io/en/latest/boto_config_tut.html) for more
    information.
  - C(AWS_REGION) or C(EC2_REGION) can be typically be used to specify the
    AWS region, when required, but this can also be defined in the
    configuration files.
---
"""

from ansible.plugins.connection import ConnectionBase, ensure_connect

from ansible.errors import AnsibleError
from ansible.utils.display import Display

import os
import botocore
import boto3


class AwsConnection(ConnectionBase):
    def __init__(self, *args, **kwargs):
        self._connection: AwsConnection
        self._display: Display()

    def _get_aws_region(self):
        region = self.get_option('region')

        if region:
            return region

        if 'AWS_REGION' in os.environ:
            return os.environ['AWS_REGION']
        if 'AWS_DEFAULT_REGION' in os.environ:
            return os.environ['AWS_DEFAULT_REGION']
        if 'EC2_REGION' in os.environ:
            return os.environ['EC2_REGION']

        try:
            profile_name = self.get_option('profile')
            return botocore.session.Session(profile=profile_name).get_config_variable('region')
        except botocore.exceptions.ProfileNotFound as e:
            raise AnsibleError("No region founds in options, aws profile, or environment variables.  A region is required.")

    def _get_aws_connection_info(self, service):

        # Check options for credentials, then check environment vars
        # access_key
        access_key = self.get_option('aws_access_key')
        secret_key = self.get_option('aws_secret_key')
        security_token = self.get_option('security_token')
        region = self.get_aws_region()
        profile_name = self.get_option('profile')

        # Only read the profile environment variables if we've *not* been passed
        # any credentials as parameters.
        if not profile_name and not access_key and not secret_key:
            if os.environ.get('AWS_PROFILE'):
                profile_name = os.environ.get('AWS_PROFILE')
            if os.environ.get('AWS_DEFAULT_PROFILE'):
                profile_name = os.environ.get('AWS_DEFAULT_PROFILE')

        if profile_name and (access_key or secret_key or security_token):
            raise AnsibleError("Passing both a profile and access tokens is not supported.")

        if not access_key:
            if os.environ.get('AWS_ACCESS_KEY_ID'):
                access_key = os.environ['AWS_ACCESS_KEY_ID']
            elif os.environ.get('AWS_ACCESS_KEY'):
                access_key = os.environ['AWS_ACCESS_KEY']
            elif os.environ.get('EC2_ACCESS_KEY'):
                access_key = os.environ['EC2_ACCESS_KEY']
            elif profile_name:
                boto3.setup_default_session(profile_name='dev')
            else:
                # in case access_key came in as empty string
                access_key = None

        if not secret_key:
            if os.environ.get('AWS_SECRET_ACCESS_KEY'):
                secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
            elif os.environ.get('AWS_SECRET_KEY'):
                secret_key = os.environ['AWS_SECRET_KEY']
            elif os.environ.get('EC2_SECRET_KEY'):
                secret_key = os.environ['EC2_SECRET_KEY']
            else:
                # in case secret_key came in as empty string
                secret_key = None

        if not security_token:
            if os.environ.get('AWS_SECURITY_TOKEN'):
                security_token = os.environ['AWS_SECURITY_TOKEN']
            elif os.environ.get('AWS_SESSION_TOKEN'):
                security_token = os.environ['AWS_SESSION_TOKEN']
            elif os.environ.get('EC2_SECURITY_TOKEN'):
                security_token = os.environ['EC2_SECURITY_TOKEN']
            else:
                # in case secret_token came in as empty string
                security_token = None

        if profile_name:
            boto_params = dict(aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None)
            boto_params['profile_name'] = profile_name

        else:
            boto_params = dict(aws_access_key_id=access_key,
                               aws_secret_access_key=secret_key,
                               security_token=security_token)

            # only set profile_name if passed as an argument
            if profile_name:
                boto_params['profile_name'] = profile_name

        client = botocore.session.Session(service, region=region, **boto_params)
        return client

    def _connect(self):
        client = self._get_aws_connection_info('cloudcontrol')
        return self
