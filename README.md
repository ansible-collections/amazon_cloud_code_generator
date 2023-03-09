# amazon_cloud_code_generator

**IMPORTANT**
The `amazon_cloud_code_generator` repository has been archived. Refer to the [`ansible.content_builder`](https://github.com/ansible-community/ansible.content_builder) instead.

`amazon_cloud_code_generator` generates the [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) from the CloudFormation Resource Type Definition Schema or meta-schema.

## Requirements

The `amazon_cloud_code_generator` relies on the CloudFormation client. Hence, the following requirements must be met:
- `boto3 >= 1.20.0`
- `botocore >= 1.23.0`
- `Python 3.9`
- `tox`

## Usage

The `amazon_cloud_code_generator` core content is hosted in the `amazon_cloud_code_generator/` directory, which contains the following subdirectories:

- `cmd/` - hosts the main logic of the `amazon_cloud_code_generator`.
    ```
    │   ├── generator.py  # Implements the logic to scrape the CloudFormation resource schema and performs all the pre-processing to produce the DOCUMENTATION block for each module
    │   ├── refresh_examples.py  # Implements the logic to update EXAMPLES block scraping all the tasks tagged with `tags: [docs]` from `amazon_cloud_code_generator/data/tests/integration/targets/`
    │   ├── refresh_modules.py  # Implements the logic to generate all the modules specified inside `resources.py` including all the utilities
    │   ├── resources.py  # Sets the AWS resource names we are going to generate  
    │   ├── utils.py  # Implements utility functions for the generator
    ```

- `config/` - Contains the `modules.yaml` file where, for each of the AWS resources we generate, an entry representing the module's name must be added. Additionally, you can also set other information that will be used in module's DOCUMENTATION like short_description, description, and so forth.

- `data/` - Contains the content that is copied to the generated collection. A high level overview of the subdirectory content is shown below:
    ```
    ├── plugins
    │   └── module_utils # Modules utils that are used by the collection plugins
    │           ├── core.py
    │           ├── utils.py
    │           └── waiters.py
    └── tests  # Contains the units and integrations tests
    │   ├── config.yml
    │   ├── integration
    │   │   ├── constraints.txt
    │   │   ├── requirements.txt
    │   │   └── targets
    │   │       ├── logs
    │   │       │   ├── aliases
    │   │       │   └── tasks
    │   │       │       └── main.yml
    │   │       ├── ...
    │   └── unit
    │       ├── constraints.txt
    │       ├── module_utils
    │       │   ├── test_core.py
    │       │   └── test_utils.py
    │       └── requirements.txt
    ```

- `templates/` - Hosts the templates files that generate each resource's plugin.
    ```
    ├── default_module.j2
    └── header.j2
    ```

The following command alllows `amazon_cloud_code_generator` to generate the content (for example, plugins, moudule_utils, tests, etc.) in the `cloud` subdirectory by default:

```python -m amazon_cloud_code_generator.cmd.refresh_modules```

A different target directory can be specified by using:

```python -m amazon_cloud_code_generator.cmd.refresh_modules --target-dir /somewhere/else```

When available, the documented EXAMPLE block of the generated modules can be updated by using the following command:

```python -m amazon_cloud_code_generator.cmd.refresh_examples```

## How to refresh the amazon.cloud collection

Fork the original [``amazon.cloud collection``](https://github.com/ansible-collections/amazon.cloud) repository to your account on GitHub. Ensure to have the path `~/.ansible/collections/ansible_collections/amazon/cloud` and clone the repository from your fork:
```
mkdir -p ~/.ansible/collections/ansible_collections/amazon/cloud
git clone https://github.com/YOUR_USER/amazon.cloud ~/.ansible/collections/ansible_collections/amazon/cloud
```

Refresh the content of the modules by changing your path to `~/.ansible/collections/ansible_collections/amazon/cloud` and running `tox -e refresh_modules`.

This command will refresh the content of the ``amazon.cloud collection`` plugins including EXAMPLE block and will format the plugins using the black formatter.
```
cd ~/.ansible/collections/ansible_collections/amazon/cloud
tox -e refresh_modules
```

You can also specify the next release version by passing the `--next-version` parameter as follows:
```
tox -e refresh_modules --next-version 0.2.0
```

Individual operations are also allowed. 

For example, you can only format the Python code of the plugins using the black formatter by running:

```tox -e black```

You can also refresh the plugins documentation located in `~/.ansible/collections/ansible_collections/amazon/cloud/docs` by running.

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
