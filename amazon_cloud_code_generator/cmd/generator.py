#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
import copy
import boto3


resources = [
    "AWS::EC2::SecurityGroup",
    "AWS::CloudWatch::Alarm",
    "AWS::EC2::Instance",
    "AWS::AutoScaling::AutoScalingGroup",
    "AWS::IAM::Policy",
    "AWS::IAM::InstanceProfile",
    "AWS::ElasticLoadBalancingV2::TargetGroup",
    "AWS::AutoScaling::ScalingPolicy",
    "AWS::EC2::SecurityGroupIngress",
    "AWS::EC2::VPCGatewayAttachment",
    "AWS::S3::BucketPolicy",
    "AWS::ElasticLoadBalancingV2::LoadBalancer",
    "AWS::ApiGateway::Deployment",
    "AWS::ApiGateway::RestApi",
    "AWS::SSM::Parameter",
    "AWS::EC2::SecurityGroupEgress",
    "AWS::RDS::DBSubnetGroup",
    "AWS::SecretsManager::Secret",
    "AWS::EC2::Volume",
    "AWS::RDS::DBCluster",
    "AWS::EKS::Nodegroup",
    "AWS::RDS::DBClusterParameterGroup",
    "AWS::EC2::VPCCidrBlock",
    "AWS::EC2::NetworkInterfaceAttachment",
    "AWS::Route53Resolver::ResolverRuleAssociation",
    "AWS::EC2::SubnetCidrBlock",
]

resources_test = ["AWS::S3::Bucket"] #, "AWS::EC2::Instance", "AWS::EC2::Volume"]


def python_type(value):
    TYPE_MAPPING = {
        "array": "list",
        "boolean": "bool",
        "integer": "int",
        "object": "dict",
        "string": "str",
    }
    return TYPE_MAPPING.get(value, value)


MODULE_NAME_MAPPING = {
    "AWS::S3::Bucket": "s3_bucket",
}


def fixup(a_dict:dict, k:str, subst_dict:dict) -> dict:
    d_copy = copy.copy(a_dict)
    
    for key in d_copy.keys():
        if key == "type":
            a_dict[key] = python_type(a_dict[key])
        if key == "description":
            a_dict[key] = [a_dict[key]]
        if key == "enum":
            a_dict["choices"] = sorted(a_dict["enum"])
        if "$ref" in key:
            lookup_param = a_dict['$ref'].split('/')[-1].strip()
            for _, _ in subst_dict.items():
                if subst_dict.get(lookup_param):
                    a_dict[key] = subst_dict[lookup_param]
        elif type(a_dict[key]) is dict:
            fixup(a_dict[key], k, subst_dict)


def cleanup_dict(d):
    d_copy = copy.copy(d)

    if not isinstance(d, dict):
        return d
    
    for k, v in d_copy.items():
        if k == "items":
            existing = d[k]
            if "$ref" in v:
                existing = d[k]["$ref"]
            del d[k]
            d["elements"] = existing
        elif k not in ("items", "properties")and isinstance(v, dict):
            if v.get("$ref"):
                d[k] = v.pop("$ref")
                print("REF AFTER",d)
        elif k == "properties":
            d["suboptions"] = d.pop(k)
        else:
            cleanup_dict(d[k])


def filter_dict(d):
    list_of_keys_to_remove = ["additionalProperties", "insertionOrder", "uniqueItems"]
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in ((k, filter_dict(v)) for k, v in d.items()) if k not in list_of_keys_to_remove}


def generate_documentation(scheme):
    module_name = MODULE_NAME_MAPPING[scheme["typeName"]]
    #description = [scheme['description']]
    documentation = {
        "module": module_name,
        "author": ["Ansible Cloud Team (@ansible-collections)"],
        #"description": description,
        "short_description": scheme['description'],
        "options": {},
        "requirements": [],
        #"version_added": added_ins["module"] or next_version,
    }
    
    documentation["options"] = scheme["definitions"]
        
    fixup(documentation, "$ref", documentation["options"])
    cleanup_dict(documentation["options"])
        
    documentation = filter_dict(documentation)
            
        #option["subptions"] = suboptions
        # option["description"] = description

        # if parameter_info.get("type"):
        #     option["type"] = python_type(parameter_info["type"])
        # if parameter_info.get("enum"):
        #     option["choices"] = sorted(parameter_info["enum"])
        # if parameter_info.get("default"):
        #     option["default"] = parameter_info.get("default")

        # documentation["options"][parameter] = option
    
    return documentation


class CloudFormationWrapper:
    """Encapsulates Amazon CloudFormation operations."""
    def __init__(self, client):
        """
        :param client: A Boto3 CloudFormation client
        """
        self.client = client
    
    def generate_docs(self, type_name):
        """
        Equivalent to
        aws cloudformation describe-type \
            --type-name My::Logs::LogGroup \
            --type RESOURCE
        """
        response = self.client.describe_type(Type='RESOURCE', TypeName=type_name)
        schema = response.get('Schema')
        documentation = generate_documentation(json.loads(schema))
        

def main():
    cloudformation = CloudFormationWrapper(boto3.client('cloudformation'))
    for type_name in resources_test:
        cloudformation.generate_docs(type_name)

if __name__ == '__main__':
    main()
    