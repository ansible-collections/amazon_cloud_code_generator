#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
import copy
import re
import yaml
import pkg_resources

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
MODULE_NAME_MAPPING = {
    "AWS::S3::Bucket": "s3_bucket",
}


def python_type(value):
    TYPE_MAPPING = {
        "array": "list",
        "boolean": "bool",
        "integer": "int",
        "object": "dict",
        "string": "str",
    }
    return TYPE_MAPPING.get(value, value)


def preprocess(a_dict, k, subst_dict):
    a_dict_copy = copy.copy(a_dict)
    
    for key in a_dict_copy.keys():
        if isinstance(a_dict[key], list):            
            if key == "enum":
                a_dict["choices"] = sorted(a_dict.pop(key))
    
        elif isinstance(a_dict_copy[key], dict):
            if  "$ref" in a_dict_copy[key]:
                lookup_param = a_dict_copy[key]['$ref'].split('/')[-1].strip()
                for _, _ in subst_dict.items():
                    if subst_dict.get(lookup_param):
                        a_dict[key] = subst_dict[lookup_param]
                    break
            else:
                preprocess(a_dict[key], k, subst_dict)
        else:
            if key == "type":
                a_dict[key] = python_type(a_dict_copy[key])
            if key == "description":
                a_dict[key] = [a_dict_copy[key]]
            if key == "const":
                a_dict["defaults"] = a_dict.pop(key)


def cleanup(a_dict):
    a_dict_copy = copy.copy(a_dict)

    if not isinstance(a_dict, dict):
        return a_dict
    
    for k, v in a_dict_copy.items():        
        if k == "properties":
            a_dict["suboptions"] = a_dict.pop(k)
    
        if isinstance(v, dict) and "required" in v and isinstance(v["required"], list):
            for r in v["required"]:
                if "properties" in a_dict[k]:
                    a_dict[k]["properties"][r]["required"] = True
                else:
                    a_dict[k]["suboptions"][r]["required"] = True
            a_dict[k].pop("required")

        cleanup(a_dict_copy[k])


def filter(a_dict):
    list_of_keys_to_remove = ["additionalProperties", "insertionOrder", "uniqueItems"]
    if not isinstance(a_dict, dict):
        return a_dict
    return {k: v for k, v in ((k, filter(v)) for k, v in a_dict.items()) if k not in list_of_keys_to_remove}


def _camel_to_snake(name, reversible=False):

    def prepend_underscore_and_lower(m):
        return '_' + m.group(0).lower()

    if reversible:
        upper_pattern = r'[A-Z]'
    else:
        # Cope with pluralized abbreviations such as TargetGroupARNs
        # that would otherwise be rendered target_group_ar_ns
        upper_pattern = r'[A-Z]{3,}s$'

    s1 = re.sub(upper_pattern, prepend_underscore_and_lower, name)
    # Handle when there was nothing before the plural_pattern
    if s1.startswith("_") and not name.startswith("_"):
        s1 = s1[1:]
    if reversible:
        return s1

    # Remainder of solution seems to be https://stackoverflow.com/a/1176023
    first_cap_pattern = r'(.)([A-Z][a-z]+)'
    all_cap_pattern = r'([a-z0-9])([A-Z]+)'
    s2 = re.sub(first_cap_pattern, r'\1_\2', s1)
    return re.sub(all_cap_pattern, r'\1_\2', s2).lower()


def camel_to_snanke(a_dict):
    b_dict = {}
    for k in a_dict.keys():
        if isinstance(a_dict[k], dict):
            b_dict[_camel_to_snake(k)] = camel_to_snanke(a_dict[k])
        else:
            b_dict[_camel_to_snake(k)] = a_dict[k]
    return b_dict


def get_module_from_config(module):
    raw_content = pkg_resources.resource_string(
        "amazon_cloud_code_generator", "config/modules.yaml"
    )
    for i in yaml.safe_load(raw_content):
        if module in i:
            return i[module]
    return False


def generate_documentation(scheme):
    module_name = MODULE_NAME_MAPPING[scheme["typeName"]]
    description = [scheme['description']]
    documentation = {
        "module": module_name,
        "author": ["Ansible Cloud Team (@ansible-collections)"],
        "description": description,
        "short_description": scheme['description'],
        "options": {},
        "requirements": [],
        # "version_added": added_ins["module"] or next_version,
    }
    
    documentation["options"] = scheme["definitions"]

    preprocess(documentation, "$ref", documentation["options"])
    cleanup(documentation["options"])
        
    documentation = filter(documentation)
    documentation = camel_to_snanke(documentation)

    module_from_config = get_module_from_config(module_name)
    if module_from_config and "documentation" in module_from_config:
        for k, v in module_from_config["documentation"].items():
            documentation[k] = v
    
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
    