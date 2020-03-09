**This project is in development**

# Cloudify Serverless Plugin

## Pre-install

Install Node.js & Serverless framework binary on your Cloudify Manager

```shell
    1  yum install -y gcc-c++ make
    2  curl -sL https://rpm.nodesource.com/setup_12.x | sudo -E bash -
    3  sudo npm install -g serverless
```

## Installation

There is only one blueprint.

  1. A simple "hello world" blueprint, `aws.yaml`.

## Function Invocation

In order to invoke function using serverless follow the `inputs.yaml` below:

```yaml
allow_kwargs_override: true
operation_kwargs:
  functions:
   - hello_1
   - hello_2
operation: 'serverless.interface.invoke'
node_instance_ids:
  - example-aws-serverless_pqua9s 
```

```shell
cfy executions start execute_operation -d aws-serverless -p inputs.yaml
```

## Uninstall 

```
cfy uninstall $deploymentid --allow-custom-parameters -p ignore_failure=true
```

## Examples
For official blueprint examples using this Cloudify plugin, please see [Cloudify Community Blueprints Examples](https://github.com/cloudify-community/blueprint-examples/).
