#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2021 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
This module_utility adds shared support for AWS Cloud Control API modules.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import botocore
from ansible_collections.amazon.aws.module_utils.core import AWSRetry


class CloudControlResource(object):

    def __init__(self, module):
        """
        Until we can use a connection plugin for auth and client setup, reuse AnsibleAWSModule
        """
        self.module = module
        self.client = module.client('cloudcontrol', retry_decorator=AWSRetry.jittered_backoff())

    def list_resources(self, type_name):
        """
        An exception occurred during task execution. To see the full traceback, use -vvv.
        The error was: botocore.exceptions.OperationNotPageableError: Operation cannot be paginated: list_resources
        """
        # paginator = self.client.get_paginator('list_resources')
        # response = paginator(TypeName=module.params.get('type_name')).build_full_result()
        try:
            response = self.client.list_resources(TypeName=type_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="")
        return response

    def get_resource(self, type_name, primary_identifier):
        # This is the "describe" equivalent for CCAPI
        try:
            response = self.client.get_resource(TypeName=type_name, Identifier=primary_identifier)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="")
        return response

    def create_resource(self, type_name, params):
        try:
            response = self.client.create_resource(TypeName=type_name, DesiredState=params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="")
        return response

    def delete_resource(self, type_name, primary_identifier):
        try:
            response = self.client.delete_resource(TypeName=type_name, Identifier=primary_identifier)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="")
        return response

    def update_resource(self, type_name, primary_identifier, params):
        try:
            response = self.client.update_resource(TypeName=type_name, Identifier=primary_identifier, PatchDocument=params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="")
        return response
