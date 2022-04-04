# amazon_cloud_code_generator

`amazon_cloud_code_generator` generates the [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) from the CloudFormation Resource Type Definition Schema or meta-schema.

## Requirements

The `amazon_cloud_code_generator` relies on the CloudFormation client. Hence, the following requirements must be met:
- `boto3 >= 1.20.0`
- `botocore >= 1.23.0`
- `Python 3.9`
- `tox`

## Usage

The [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) modules are built using:

```tox -e refresh_modules```

The modules will be generated in the `cloud` subdirectory by default. A different target directory can be specified by using:

```tox -e refresh_modules --target-dir /somewhere/else```

Whether available, the documented EXAMPLE block of the generated modules can be updated by using the following command:

```tox -e refresh_examples --target-dir /somewhere/else```

This information is scraped from the tests/ directory.

## How to refresh the amazon.cloud collection

Clone the original [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) from GitHub:
```
mkdir -p ~/.ansible/collections/ansible_collections/amazon/cloud
git clone https://github.com/ansible-collections/amazon.cloud ~/.ansible/collections/ansible_collections/amazon/cloud
```

Refresh the content of the modules moving in the repository path:
```
cd ~/.ansible/collections/ansible_collections/amazon/cloud
tox -e refresh_modules
```
Format the Python code of the modules using the black formatter:

```tox -e black```

Refresh the modules documentation localed in `~/.ansible/collections/ansible_collections/amazon/cloud/docs`.

```tox -e add_docs```

Run `ansible-test` to validate the result using:
```
virtualenv -p python3.9 ~/tmp/venv-tmp-py39-aws
source ~/tmp/venv-tmp-py39-aws/bin/activate
pip install -r requirements.txt -r test-requirements.txt ansible
ansible-test sanity --requirements --local --python 3.9 -vvv
```

## Code of Conduct

This project is governed by the [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
                                                                              