#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


RESOURCES = [
    "AWS::S3::Bucket",
    "AWS::Logs::LogGroup",
    "AWS::IAM::Role",
    "AWS::EC2::RouteTable",
    "AWS::EC2::VPC",
    "AWS::EC2::Subnet",
    "AWS::EC2::InternetGateway",
    "AWS::EC2::SubnetRouteTableAssociation",
]


MODULE_NAME_MAPPING = {
    "AWS::S3::Bucket": "s3_bucket",
    "AWS::Logs::LogGroup": "logs_log_group",
    "AWS::IAM::Role": "iam_role",
    "AWS::EC2::RouteTable": "ec2_route_table",
    "AWS::EC2::VPC": "ec2_vpc",
    "AWS::EC2::Subnet": "ec2_subnet",
    "AWS::EC2::InternetGateway": "ec2_internet_gateway",
    "AWS::EC2::SubnetRouteTableAssociation": "ec2_subnet_route_table_association",
}
