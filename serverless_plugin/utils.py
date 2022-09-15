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
import sys

from cloudify.utils import exception_to_error_cause
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import get_node_instance_dir
from cloudify_common_sdk.secure_property_management import get_stored_property

from serverless_sdk import Serverless

SL_CONFIG = 'serverless_config'
SERVERLESS_PARAMS = [
    'serverless_config',
    'resource_config',
    'client_config',
]
ROOT_DIR = 'root_directory'
BINARY_TYPE = 'cloudify.nodes.serverless.Binary'


def initialize_serverless(_ctx):
    params = dict(
        deployment_name=_ctx.deployment.id,
        node_instance_name=_ctx.instance.id,
        logger=_ctx.logger
    )
    if ROOT_DIR not in _ctx.instance.runtime_properties:
        _ctx.instance.runtime_properties[ROOT_DIR] = get_node_instance_dir()
    params[ROOT_DIR] = _ctx.instance.runtime_properties[ROOT_DIR]
    if BINARY_TYPE not in _ctx.node.type_hierarchy:
        for key in SERVERLESS_PARAMS:
            params[key] = get_stored_property(_ctx, key)
    else:
        if SL_CONFIG not in params:
            params[SL_CONFIG] = get_stored_property(_ctx, SL_CONFIG)
        if not _ctx.node.properties['use_external_resource'] and \
                params[SL_CONFIG].get('executable_path') and \
                _ctx.workflow_id == 'install':
            raise NonRecoverableError(
                'The parameter executable_path should only be provided when '
                'use_external_resource is True. Params: {}.'.format(
                    params
                ))
        elif _ctx.workflow_id == 'install':
            return Serverless(**params)
    params[SL_CONFIG] = verify_executable(
        params[SL_CONFIG], _ctx.instance)
    return Serverless(**params)


def verify_executable(config, node_instance=None):
    executable_from_config = config.get('executable_path')
    if validate_executable_file(executable_from_config):
        return config
    if node_instance:
        executable_from_runtime_props = node_instance.runtime_properties.get(
            'executable_path')
        if validate_executable_file(executable_from_runtime_props):
            config['executable_path'] = executable_from_runtime_props
            return config
        rels = find_rels_by_node_type(node_instance, BINARY_TYPE)
        if len(rels) == 1:
            executable_from_rel = \
                rels[0].target.instance.runtime_properties.get(
                    'executable_path')
            if validate_executable_file(executable_from_rel):
                node_instance.runtime_properties['executable_path'] = \
                    executable_from_rel # Save it in runtime props so that we don't have to search relationships again. # noqa
                config['executable_path'] = executable_from_rel
                return config
    raise NonRecoverableError('Failed to locate valid serverless executable.')


def validate_executable_file(file_path):
    if not file_path:
        return False
    if not os.path.exists(file_path):
        raise NonRecoverableError(
            'Executable file_path {} was provided, '
            'but the file does not exist.'.format(file_path))
    if not os.access(file_path, os.X_OK):
        raise NonRecoverableError(
            'Executable file_path {} was provided, '
            'but the file is not executable.'.format(file_path))
    return True


def find_rels_by_node_type(node_instance, node_type):
    return [n for n in node_instance.relationships
            if node_type in n.target.node.type_hierarchy]


def generate_traceback_exception():
    _, exc_value, exc_traceback = sys.exc_info()
    response = exception_to_error_cause(exc_value, exc_traceback)
    return response
