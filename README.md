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

When available, the documented EXAMPLE block of the generated modules can be updated by using the following command:

```tox -e refresh_examples --target-dir /somewhere/else```

This information is scraped from the tests/ directory.

## How to refresh the amazon.cloud collection

Fork the original [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) repository to your account on GitHub. Clone the repository from your fork:
```
mkdir -p ~/.ansible/collections/ansible_collections/amazon/cloud
git clone https://github.com/YOUR_USER/amazon.cloud ~/.ansible/collections/ansible_collections/amazon/cloud
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

Run `ansible-test` to validate the generated content using:
```
virtualenv -p python3.9 ~/tmp/venv-tmp-py39-aws
source ~/tmp/venv-tmp-py39-aws/bin/activate
pip install -r requirements.txt -r test-requirements.txt ansible
ansible-test sanity --requirements --local --python 3.9 -vvv
```

You can also execute all integration tests for the collection using:
```
ansible-test integration --requirements --docker

```

## Contributing
We welcome community contributions and if you find problems, please open an issue or create a Pull Request. You can also join us in the:
    - `#ansible-aws` [irc.libera.chat](https://libera.chat/) channel
    - `#ansible` (general use questions and support), `#ansible-community` (community and collection development questions), and other [IRC channels](https://docs.ansible.com/ansible/devel/community/communication.html#irc-channels).

The Amazon Web Services Working groups is holding a monthly community meeting at `#ansible-aws` IRC channel at 17:30 UTC every fourth Thursday of the month. If you have something to discuss (e.g. a PR that needs help), add your request to the [meeting agenda](https://github.com/ansible/community/issues/654) and join the IRC `#ansible-aws` channel. Invite (import by URL): [ics file](https://raw.githubusercontent.com/ansible/community/main/meetings/ical/aws.ics)

You don't know how to start? Refer to our [contribution guide](CONTRIBUTING.md)!

## Code of Conduct

This project is governed by the [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
                                                                              