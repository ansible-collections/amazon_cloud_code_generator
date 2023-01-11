# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import os
import json
from pathlib import Path

import gouttelette.cmd.generator as g
import gouttelette.cmd.refresh_modules as rm
import gouttelette.cmd.refresh_schema as rs


def resources(filepath):
    current = Path(os.path.dirname(os.path.abspath(__file__)))
    with open(current / filepath) as fp:
        return json.load(fp)


raw_content = resources("fixtures/raw_content.json")
expected_content = resources("fixtures/expected_content.json")


def test_Description_normalize():
    assert g.Description.normalize("a") == ["a."]
    assert g.Description.normalize("") == []
    assert g.Description.normalize("CloudWatch") == ["CloudWatch."]
    assert g.Description.normalize(
        "The Amazon Resource Name (ARN) of the Amazon SQS queue to which Amazon S3 publishes a message."
    ) == [
        "The Amazon Resource Name (ARN) of the Amazon SQS queue to which Amazon S3 publishes a message."
    ]
    assert g.Description.normalize(
        "Setting this element to TRUE causes Amazon S3 to reject calls to PUT Bucket policy."
    ) == [
        "Setting this element to C(True) causes Amazon S3 to reject calls to PUT Bucket policy."
    ]
    assert g.Description.normalize(
        "Setting this element to TRUE causes Amazon S3 to reject calls to PUT Bucket policy"
    ) == [
        "Setting this element to C(True) causes Amazon S3 to reject calls to PUT Bucket policy."
    ]
    assert g.Description.normalize(
        "Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653."
    ) == [
        "Possible values are: C(1), C(3), C(5), C(7), C(14), C(30), C(60), C(90), C(120), C(150), C(180), C(365), C(400), C(545), C(731), C(1827), and C(3653)."
    ]
    assert g.Description.normalize(
        "Container for the transition rule that describes when noncurrent objects transition to the STANDARD_IA, ONEZONE_IA, INTELLIGENT_TIERING, GLACIER_IR, C(GLACIER), or DEEP_ARCHIVE storage class."
    ) == [
        "Container for the transition rule that describes when noncurrent objects transition to the C(STANDARD_IA), C(ONEZONE_IA), C(INTELLIGENT_TIERING), C(GLACIER_IR), C(GLACIER), or C(DEEP_ARCHIVE) storage class."
    ]


def test_generate_documentation():
    schema = rs.generate_schema(json.dumps(raw_content))
    module = rm.AnsibleModuleBaseAmazon(schema=schema)
    added_ins = {"module": "1.0.0"}
    documentation = g.generate_documentation(
        module,
        added_ins,
        "1.0.0",
        Path(os.path.dirname(os.path.abspath(__file__)) + "/fixtures"),
    )
    assert documentation == expected_content
