import argparse
import pathlib
from typing import Dict, Iterable, List, Optional, TypedDict
import boto3
from .resources import RESOURCES
from .generator import CloudFormationWrapper
import json
from .utils import camel_to_snake


class Schema(TypedDict):
    """A type for the JSONSchema spec"""

    typeName: str
    description: str
    properties: Dict
    definitions: Optional[Dict]
    required: Optional[List]
    primaryIdentifier: List
    readOnlyProperties: Optional[List]
    createOnlyProperties: Optional[List]
    taggable: Optional[bool]
    handlers: Optional[Dict]


def generate_schema(raw_content) -> Dict:
    json_content = json.loads(raw_content)
    schema: Dict[str, Schema] = json_content

    for key, value in schema.items():
        if key != "anyOf":
            if isinstance(value, list):
                elems = []
                for v in value:
                    if isinstance(v, list):
                        elems.extend(
                            [camel_to_snake(p.split("/")[-1].strip()) for p in v]
                        )
                    else:
                        elems.append(camel_to_snake(v.split("/")[-1].strip()))

                schema[key] = elems

    return schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect the schema definition.")
    parser.add_argument(
        "--schema-dir",
        type=pathlib.Path,
        default=pathlib.Path("amazon_cloud_code_generator/api_specifications"),
        help="location where to store the collected schemas (default: ./amazon_cloud_code_generator/api_specifications)",
    )
    args = parser.parse_args()

    for type_name in RESOURCES:
        print("Collecting Schema")
        print(type_name)
        cloudformation = CloudFormationWrapper(boto3.client("cloudformation"))
        raw_content = cloudformation.generate_docs(type_name)
        schema = generate_schema(raw_content)
        schema_file = args.schema_dir / f"{type_name}.json"
        schema_file.write_text(json.dumps(schema))


if __name__ == "__main__":
    main()
