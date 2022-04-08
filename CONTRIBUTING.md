# Contributing

## Getting Started

General information about setting up your Python environment, testing modules,
Ansible coding styles, and more can be found in the [Ansible Community Guide](
https://docs.ansible.com/ansible/latest/community/index.html).

Information about AWS SDK library usage, module utils, testing, and more can be
found in the [AWS Guidelines](https://docs.ansible.com/ansible/devel/dev_guide/platforms/aws_guidelines.html)
documentation.


## Submitting Issues 

`amazon_cloud_code_generator` is used to generate the `amazon.cloud` collection from the CloudFormation Resource Type Definition Schema or meta-schema.

All software has bugs, and the `amazon_cloud_code_generator` is no exception. When you find a bug, 
you can help tremendously by [telling us about it](https://github.com/ansible-collections/amazon_cloud_code_generator/issues/new/choose).


If you should discover that the bug you're trying to file already exists in an issue, 
you can help by verifying the behavior of the reported bug with a comment in that 
issue, or by reporting any additional information

## Pull Requests

Because `amazon_cloud_code_generator` is used to generate the [`amazon.cloud`](https://github.com/ansible-collections/amazon.cloud) collection, if you find problems, please, open Pull Requests against this repository.

Bug fixes for [module_utils](https://github.com/ansible-collections/amazon_cloud_code_generator/tree/main/amazon_cloud_code_generator/data) shared between the `amazon.cloud` modules that currently have integration tests or unit tests SHOULD include additional integration or unit tests that exercises the affected behaviour.

Bug fixes for [generator code](https://github.com/ansible-collections/amazon_cloud_code_generator/tree/main/amazon_cloud_code_generator/cmd) SHOULD also have unit tests that exercises the affected behaviour.

## Code of Conduct
The `amazon.cloud` collection follows the Ansible project's 
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html). 
Please read and familiarize yourself with this document.

## IRC
Our IRC channels may require you to register your nickname. If you receive an error when you connect, see 
[Libera.Chat's Nickname Registration guide](https://libera.chat/guides/registration) for instructions.

The `#ansible-aws` channel on [irc.libera.chat](https://libera.chat/) is the main and official place to discuss use and development
of the `amazon.cloud` collection.
