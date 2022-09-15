# Copyright (c) 2020 - 2022 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from . import decorators


def _download_handlers(ctx, handler_path, target_path):
    ctx.download_resource(handler_path, target_path)


BINARY_NAME = "serverless"


@operation
@decorators.with_serverless
def create(serverless, **_):
    serverless.create()


@operation
@decorators.with_serverless
def configure(ctx, serverless, **_):
    for function in serverless.functions:
        filepath = function.get('path')
        if not filepath:
            raise NonRecoverableError(
                'Function path does not exist. '
                'Provided function: {}'.format(function))
        filename = os.path.basename(filepath)
        _download_handlers(
            ctx,
            filepath,
            os.path.join(serverless.root_directory, filename)
        )
    serverless.configure()


@operation
@decorators.with_serverless
def start(serverless, **_):
    serverless.deploy()


@operation
@decorators.with_serverless
def poststart(ctx, serverless, **_):
    ctx.instance.runtime_properties['info'] = serverless.info()


@operation
@decorators.with_serverless
def stop(serverless, **_):
    serverless.destroy()


@operation
@decorators.with_serverless
def delete(serverless, **_):
    serverless.clean()


@operation
@decorators.with_serverless
def invoke(serverless, **_):
    for function in serverless.functions:
        serverless.invoke(function['name'])


@operation
@decorators.with_serverless
def metrics(serverless, **_):
    if not serverless.functions:
        serverless.metrics()
    else:
        for function in serverless.functions:
            serverless.metrics(function['name'])


@operation
@decorators.with_serverless
def install_binary(ctx, serverless, **_):
    if not ctx.node.properties.get('use_external_resource'):
        installation_dir = serverless.root_directory
        installation_source = ctx.node.properties.get('installation_source')
        if installation_source:
            serverless.install_binary(
                ctx.node.properties.get('installation_source'),
                installation_dir,
                os.path.join(installation_dir, BINARY_NAME),
                )
            ctx.instance.runtime_properties['executable_path'] = os.path.join(
                installation_dir, BINARY_NAME)
        else:
            serverless.install_with_npm()
            ctx.instance.runtime_properties['executable_path'] = \
                serverless.executable_path


@operation
@decorators.with_serverless
def uninstall_binary(ctx, serverless, **_):
    if not ctx.node.properties.get('use_external_resource'):
        serverless.uninstall_binary()
