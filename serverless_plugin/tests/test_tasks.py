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

import shutil
import logging
import unittest
import tempfile

import mock
from cloudify.state import current_ctx

from .. import tasks

TEST_SERVERLESS_CONFIG = {
    'executable_path': 'foo',
}
TEST_CLIENT_CONFIG = {
    'provider': 'foobar',
    'credentials': {
        'key': 'secret_name',
        'secret': 'super_secret',
    }
}
TEST_RESOURCE_CONFIG = {
    'name': 'bar',
    'template': 'baz',
    'template_url': '',
    'template_path': '',
    'functions': [
        {
            'name': 'qux',
            'handler': 'quux',
            'events': [
                'bongo',
            ],
            'environment': {
                'taco': 'bell',
            }
        }
    ]
}


class ServerlessTestBase(unittest.TestCase):

    @staticmethod
    def get_mock_ctx(runtime_properties=None, op_name=None):
        node_properties = {
            'use_external_resource': False,
            'client_config': TEST_CLIENT_CONFIG,
            'serverless_config': TEST_SERVERLESS_CONFIG,
            'resource_config': TEST_RESOURCE_CONFIG
        }
        mock_node = mock.Mock(
            id='test_sl',
            name='test_sl',
            properties=node_properties)
        mock_instance = mock.Mock(
            id='test_sl_012345',
            runtime_properties=runtime_properties or {},
        )
        mock_op = mock.Mock(
            name=op_name or 'cloudify.interfaces.lifecycle.create'
        )
        return mock.Mock(
            node=mock_node,
            operation=mock_op,
            instance=mock_instance,
            logger=logging.getLogger(__name__),
        )

    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_plugin.utils.get_node_instance_dir')
    @mock.patch('serverless_sdk.run_subprocess')
    def test_create(self, get_stored_prop, get_dir, *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            ctx.node.properties.get('resource_config'),
            ctx.node.properties.get('serverless_config')
        ]
        temp_dir = tempfile.mkdtemp()
        get_dir.return_value = temp_dir
        tasks.create(ctx=ctx)
        shutil.rmtree(temp_dir)
