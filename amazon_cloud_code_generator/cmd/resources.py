#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


RESOURCES = [
    "AWS::S3::Bucket",
    "AWS::Logs::LogGroup",
    "AWS::IAM::Role",
]


MODULE_NAME_MAPPING = {
    "AWS::S3::Bucket": "s3_bucket",
    "AWS::Logs::LogGroup": "logs_log_group",
    "AWS::IAM::Role": "iam_role",
}
