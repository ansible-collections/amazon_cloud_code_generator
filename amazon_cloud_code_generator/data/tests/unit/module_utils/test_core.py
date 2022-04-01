import json
from unittest.mock import MagicMock, Mock

import pytest

from amazon_cloud_code_generator.module_utils.core import CloudControlResource


@pytest.fixture
def ccr():
    class NotFound(Exception):
        pass

    resource = CloudControlResource(Mock())
    resource.module.check_mode = False
    resource.module.params = {"wait_timeout": 5}
    resource.client = MagicMock()
    resource.client.exceptions.ResourceNotFoundException = NotFound
    return resource


def test_present_creates_resource(ccr):
    ccr.client.get_resource.side_effect = (
        ccr.client.exceptions.ResourceNotFoundException()
    )
    params = {"BucketName": "test_bucket"}
    changed = ccr.present("AWS::S3::Bucket", "test_bucket", params)
    assert changed
    ccr.client.create_resource.assert_called_with(
        TypeName="AWS::S3::Bucket", DesiredState=json.dumps(params)
    )
    ccr.client.update_resource.assert_not_called()


def test_present_updates_resource(ccr):
    resource = {
        "TypeName": "AWS::S3::Bucket",
        "ResourceDescription": {
            "Identifier": "test_bucket",
            "Properties": '{"BucketName": "test_bucket"}',
        },
    }
    ccr.client.get_resource.return_value = resource
    params = {"BucketName": "test_bucket", "Tags": [{"Key": "k", "Value": "v"}]}
    changed = ccr.present("AWS::S3::Bucket", "test_bucket", params)
    assert changed
    ccr.client.update_resource.assert_called_with(
        TypeName="AWS::S3::Bucket",
        Identifier="test_bucket",
        PatchDocument='[{"op": "add", "path": "/Tags", "value": [{"Key": "k", "Value": "v"}]}]',
    )
    ccr.client.create_resource.assert_not_called()
