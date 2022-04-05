# 2. Limit dependence on amazon.aws collection

Date: 2022-03-30

## Status

Accepted

## Context

The amazon.cloud collection will need to use some functionality that currently exists in the amazon.aws collection. The community.aws collection has similar needs, and already imports from amazon.aws. Inter-collection dependencies add a burden on testing, releasing and deployment, so we should carefully consider how and when to use this.

We considered three options:

1. Copy any code from amazon.aws to cloud.amazon. This has the advantage of no collection dependencies, but leads to duplicated code.
2. Import directly from amazon.aws (create a dependency on amazon.aws). This is the least amount of effort up front, but increases the testing and maintenance burden by creating a dependency on another collection.
3. Migrate shared code from amazon.aws to cloud.common and import from there (create a dependency on cloud.common). In the future, if we were to use turbo mode, we would already have a dependency on cloud.common. If we migrated the shared parts of amazon.aws to cloud.common and had amazon.aws, community.aws and amazon.cloud import from there, we would at least minimize the collection dependencies. Given the impact this change would have, this is not viable in the short term.

In addition, it's possible we may move to a connection plugin method for boto3 client authentication in the future, which may remove the need for the AnsibleAWSModule.

## Decision

We will import AnsibleAWSModule from amazon.aws and copy the remaining functions. Given the size and scope of AnsibleAWSModule, attempting to duplicate this code would likely lead to larger maintenance problems as time goes on. The remaining code that is copied consists of a handful of small functions.

This decision should be revisisted in the future if we find that we need to import/copy significantly more code.

## Consequences

If there are breaking changes in imported code, we'll need to ensure we coordinate the release of collections. As the amount of code being copied is small, it's not expected there should be much associated maintenance, but we could end up having to propagate bugfixes across collections.
