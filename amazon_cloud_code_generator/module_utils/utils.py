import json

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


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


class JsonPatch(list):
    def __str__(self):
        return json.dumps(self)


def list_merge(old, new):
    l = []
    for i in old + new:
        if i not in l:
            l.append(i)
    return l


def op(operation, path, value):
    path = "/{0}".format(path.lstrip("/"))
    return {"op": operation, "path": path, "value": value}


# This is a rather naive implementation. Dictionaries within
# lists and lists within dictionaries will not be merged.
def make_op(path, old, new, strategy):
    if isinstance(old, dict):
        if strategy == "merge":
            new = dict(old, **new)
    elif isinstance(old, list):
        if strategy == "merge":
            new = list_merge(old, new)
    return op("replace", path, new)
