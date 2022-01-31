#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
import re

import boto3
import copy


SCHEMAS_DIR = './aws_cloudformation_schemas/'
SCHEMA_DEFINITION = 'provider.definition.schema.v1.json'

with open(SCHEMA_DEFINITION, 'r') as f:
    provider_schema = json.loads(f.read())



'''
What schema keys do we need to process:

In [13]: schema.keys()                                                                                                                                                                                                                       
Out[13]: dict_keys(['$schema', # Don't need
'$id',  # Don't need?
'title',  # Don't need?
'description',  # Don't need
'definitions',  # Super important
'type',  # Critical
'patternProperties', # Unsure?
'properties',  # Critical
'required',  # Critical
'additionalProperties' # Probably important
])

In [19]: schema['properties'].keys()                                                                                                                                                                                                         
['$schema',   # No
 'type',  # Unknown
 'typeName',  # Critical - "AWS::Logs::LogGroup"
 '$comment',  # meh
 'title',  # meh  
 'description',   # meh?
 'sourceUrl',  # meh, maybe in the header?
 'documentationUrl',  # meh, it's missing in a lot of cases
 'replacementStrategy',  # This is interesting. Few uses, so look at aws-ec2-vpcdhcpoptionsassociation.json
 'taggable',  # yep
 'tagging',  # definitely
 'additionalProperties',  # probably but I think this is the one that's for 3rd party schemas?
 'properties',  # definitely
 'definitions',  #  probably, look at usage beyond tags?
 'propertyTransform',  # Yes, see aws-ecs-capacityprovider.json
 'handlers',  # yes
 'remote',  # No? "Reserved for CloudFormation use. A namespace to inline remote schemas."
 'readOnlyProperties', # Yep, whole lotta decision making based on the following
 'writeOnlyProperties',
 'conditionalCreateOnlyProperties',
 'nonPublicProperties',
 'nonPublicDefinitions',
 'createOnlyProperties',
 'deprecatedProperties',
 'primaryIdentifier',  # Very important
 'additionalIdentifiers',  # Maybe??
 'required',  # These are sort of like validations, but they apply to options and suboptions (properties of definitions)
 'allOf',  # not documented, thanks amazon. the 2 places it's implemented don't help, see those APIs I guess
 'anyOf',  # this might be a weird "choices" thing?  I think it's a way of saying, "0(1?) or more of these subopts" 
 'oneOf',
 'resourceLink',   #  I don't think we care?
 'typeConfiguration'  #  Not until we allow 3rd party "to set the configuration data for registry types. ... not passed through the resource properties in template. ... possible use cases is ... 3P resource providers.",
 ]

'''

# Map CCAPI handlers to Ansible module 'state' values, handler is a sub of properties
handler_mapping = {
    'create': 'create',
    'read': 'get',  ## GET is what's in the AWS blog posts/docs so we should go with that
    'update': 'update',
    'delete': 'delete',
    'list': 'list'
}


'''
We'll need to ignore lists but generally use to template the params dict in the module:
In [11]: with open('amazon_cloud_code_generator/aws_cloudformation_schemas/aws-s3-bucket.json', 'r') as f: 
    ...:     foo = json.loads(f.read()) 

In [32]: for i in foo['properties'].keys(): 
    ...:     ff = "params['{0}'] = module.params.get('{1}')".format(i, _camel_to_snake(i)) 
    ...:     print(ff) 
    ...:                                                                                                                                                                                                                                     
params['AccelerateConfiguration'] = module.params.get('accelerate_configuration')
params['AccessControl'] = module.params.get('access_control')
params['AnalyticsConfigurations'] = module.params.get('analytics_configurations')
params['BucketEncryption'] = module.params.get('bucket_encryption')
params['BucketName'] = module.params.get('bucket_name')
---snip---
'''

def _camel_to_snake(name, reversible=False):
    # From https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/common/dict_transformations.py
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
    """
    function inspired by another answers linked below
    """ 
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
    