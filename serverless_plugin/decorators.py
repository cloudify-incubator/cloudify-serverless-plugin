# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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
import sys

from functools import wraps

from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

from serverless_sdk import Serverless


def with_serverless(func):
    @wraps(func)
    def function(*args, **kwargs):
        ctx = kwargs['ctx']
        operation_name = ctx.operation.name
        provider_config = ctx.node.properties['provider_config']
        executable_path = ctx.node.properties['executable_path']
        service_config = ctx.node.properties['service_config']
        functions = ctx.node.properties['functions']
        variables = ctx.node.properties.get('variables')
        if not os.path.exists(executable_path):
            raise NonRecoverableError(
                "Serverless's executable not found in {0}. Please set the "
                "'executable_path' property accordingly.".format(
                    executable_path))
        serverless = Serverless(
            ctx.logger,
            provider_config,
            service_config,
            functions,
            executable_path,
            variables
        )
        kwargs['serverless'] = serverless
        try:
            func(*args, **kwargs)
        except Exception as error:
            _, _, tb = sys.exc_info()
            raise NonRecoverableError(
                'Failure while trying to run operation'
                '{0}: {1}'.format(operation_name, error.message),
                causes=[exception_to_error_cause(error, tb)])
    return function
