#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


RESOURCES = [
    "AWS::S3::Bucket",
    #"AWS::EC2::SecurityGroup",
    # "AWS::CloudWatch::Alarm",
    "AWS::EC2::Instance",
    # "AWS::AutoScaling::AutoScalingGroup",
    "AWS::IAM::Policy",
    # "AWS::IAM::InstanceProfile",
    # "AWS::ElasticLoadBalancingV2::TargetGroup",
    # "AWS::AutoScaling::ScalingPolicy",
    # "AWS::EC2::SecurityGroupIngress",
    # "AWS::EC2::VPCGatewayAttachment",
    # "AWS::S3::BucketPolicy",
    # "AWS::ElasticLoadBalancingV2::LoadBalancer",
    # "AWS::ApiGateway::Deployment",
    # "AWS::ApiGateway::RestApi",
    # "AWS::SSM::Parameter",
    # "AWS::EC2::SecurityGroupEgress",
    # "AWS::RDS::DBSubnetGroup",
    # "AWS::SecretsManager::Secret",
    # "AWS::EC2::Volume",
    # "AWS::RDS::DBCluster",
    # "AWS::EKS::Nodegroup",
    # "AWS::RDS::DBClusterParameterGroup",
    # "AWS::EC2::VPCCidrBlock",
    # "AWS::EC2::NetworkInterfaceAttachment",
    # "AWS::Route53Resolver::ResolverRuleAssociation",
    # "AWS::EC2::SubnetCidrBlock",
]


MODULE_NAME_MAPPING = {
    "AWS::S3::Bucket": "s3_bucket",
    "AWS::IAM::Policy": "iam_policy",
    "AWS::EC2::Instance": "ec2_instance",
}
