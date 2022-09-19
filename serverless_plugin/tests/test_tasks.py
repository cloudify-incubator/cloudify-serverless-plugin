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
import shutil
import logging
import unittest
import tempfile
from pathlib import Path
from copy import deepcopy
from functools import wraps

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
            properties=node_properties,
            type_hierarchy=[
                'cloudify.nodes.Root',
                'cloudify.nodes.serverless.Service'
            ]
        )

        mock_instance = mock.Mock(
            id='test_sl_012345',
            runtime_properties=runtime_properties or {},
        )
        mock_op = mock.Mock(
            name=op_name or 'cloudify.interfaces.lifecycle.create'
        )

        logger = logging.getLogger(__name__)

        def mock_dr(source, target):
            logger.info("Downloading source to target: {} {}".format(
                source, target))
            Path(target).touch()

        return mock.Mock(
            node=mock_node,
            operation=mock_op,
            instance=mock_instance,
            logger=logger,
            download_resource=mock_dr
        )

    @staticmethod
    def get_binary_type_mock_ctx(runtime_properties=None, op_name=None):
        node_properties = {
            'use_external_resource': False,
            'serverless_config': {
                'executable_path': '',
            },
            'installation_source': 'https://github.com/serverless/serverless/'
                                   'releases/download/v3.22.0/'
                                   'serverless-linux-x64',
        }
        mock_node = mock.Mock(
            id='test_sl',
            name='test_sl',
            properties=node_properties,
            type_hierarchy=[
                'cloudify.nodes.Root',
                'cloudify.nodes.serverless.Binary'
            ]
        )

        mock_instance = mock.Mock(
            id='test_sl_012345',
            runtime_properties=runtime_properties or {},
        )
        mock_op = mock.Mock(
            name=op_name or 'cloudify.interfaces.lifecycle.create'
        )

        logger = logging.getLogger(__name__)

        def mock_dr(source, target):
            logger.info("Downloading source to target: {} {}".format(
                source, target))
            Path(target).touch()

        return mock.Mock(
            node=mock_node,
            operation=mock_op,
            instance=mock_instance,
            logger=logger,
            download_resource=mock_dr,
            workflow_id='install',
        )

    def _test_wrapper(func):
        """Add handling for removing test dir and other common objs
        That should be recreated for every individual test.
        :return:
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with mock.patch('serverless_plugin.utils.'
                            'get_node_instance_dir') as get_dir:
                temp_dir = tempfile.mkdtemp()
                get_dir.return_value = temp_dir
                try:
                    func(*args, **kwargs)
                finally:
                    shutil.rmtree(temp_dir)
        return wrapper

    @_test_wrapper
    @mock.patch('serverless_sdk.Serverless.tempenv')
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_create(self,
                    run_sub,
                    get_stored_prop,
                    verify,
                    tempenv,
                    *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            ctx.node.properties.get('resource_config'),
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.create(ctx=ctx)
        run_sub.assert_called_with(
            [
                'serverless',
                'create',
                '--name',
                'bar',
                '--template',
                'baz',
            ],
            ctx.instance.runtime_properties['root_directory'],
            additional_args={
                'env': {},
                'log_stdout': True,
            },
            env={
                'TMP': tempenv,
                'TEMP': tempenv,
                'TMPDIR': tempenv,
            },
            return_output=True
        )

    @_test_wrapper
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_configure(self, run_sub, get_stored_prop, verify, *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        resource_config = deepcopy(TEST_RESOURCE_CONFIG)
        resource_config['functions'][0]['path'] = 'foo_path'
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            resource_config,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.configure(ctx=ctx)
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    ctx.instance.runtime_properties['root_directory'],
                    'foo_path'
                )
            )
        )

    @_test_wrapper
    @mock.patch('serverless_sdk.Serverless.tempenv')
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_start(self, run_sub, get_stored_prop, verify, tempenv, *_, **__):

        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            TEST_RESOURCE_CONFIG,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.start(ctx=ctx)
        run_sub.assert_called_with(
                [
                    'serverless',
                    'deploy',
                ],
                ctx.instance.runtime_properties['root_directory'],
                additional_args={
                    'env': {},
                    'log_stdout': True
                },
                env={
                    'TMP': tempenv,
                    'TEMP': tempenv,
                    'TMPDIR': tempenv,
                },
                return_output=True
        )

    @_test_wrapper
    @mock.patch('serverless_sdk.Serverless.tempenv')
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_stop(self, run_sub, get_stored_prop, verify, tempenv, *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            TEST_RESOURCE_CONFIG,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.stop(ctx=ctx)
        run_sub.assert_called_with(
                [
                    'serverless',
                    'remove',
                ],
                ctx.instance.runtime_properties['root_directory'],
                additional_args={
                    'env': {},
                    'log_stdout': True
                },
                env={
                    'TMP': tempenv,
                    'TEMP': tempenv,
                    'TMPDIR': tempenv,
                },
                return_output=True
        )

    @_test_wrapper
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_delete(self, run_sub, get_stored_prop, verify, *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            TEST_RESOURCE_CONFIG,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.delete(ctx=ctx)
        self.assertFalse(run_sub.called)

    @_test_wrapper
    @mock.patch('serverless_sdk.Serverless.tempenv')
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_invoke(self, run_sub, get_stored_prop, verify, tempenv, *_, **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            TEST_RESOURCE_CONFIG,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.invoke(ctx=ctx)
        run_sub.assert_called_with(
                [
                    'serverless',
                    'invoke',
                    '--function',
                    'qux',
                ],
                ctx.instance.runtime_properties['root_directory'],
                additional_args={
                    'env': {},
                    'log_stdout': True,
                },
                env={
                    'TMP': tempenv,
                    'TEMP': tempenv,
                    'TMPDIR': tempenv,
                },
                return_output=True
        )

    @_test_wrapper
    @mock.patch('serverless_sdk.Serverless.tempenv')
    @mock.patch('serverless_plugin.utils.verify_executable')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_metrics(
            self,
            run_sub,
            get_stored_prop,
            verify,
            tempenv,
            *_,
            **__):
        ctx = self.get_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('client_config'),
            TEST_RESOURCE_CONFIG,
            ctx.node.properties.get('serverless_config')
        ]
        verify.return_value = dict(executable_path='serverless')
        tasks.metrics(ctx=ctx)
        run_sub.assert_called_with(
                [
                    'serverless',
                    'metrics',
                    '--function',
                    'qux',
                ],
                ctx.instance.runtime_properties['root_directory'],
                additional_args={
                    'env': {},
                    'log_stdout': True
                },
                env={
                    'TMP': tempenv,
                    'TEMP': tempenv,
                    'TMPDIR': tempenv,
                },
                return_output=True
        )

    @_test_wrapper
    @mock.patch('cloudify_common_sdk.utils.run_subprocess')
    @mock.patch('serverless_plugin.utils.get_stored_property')
    @mock.patch('serverless_sdk.Serverless._execute')
    def test_install_binary(self,
                            run_sub,
                            get_stored_prop,
                            run_sub_sdk,
                            *_, **__):
        ctx = self.get_binary_type_mock_ctx()
        current_ctx.set(ctx=ctx)
        get_stored_prop.side_effect = [
            ctx.node.properties.get('serverless_config')
        ]
        tasks.install_binary(ctx=ctx)

        download_call = mock.call(
            [
                'curl',
                '-L',
                '-o',
                os.path.join(
                    ctx.instance.runtime_properties['root_directory'],
                    'serverless'
                ),
                ctx.node.properties['installation_source']
            ]
        )
        chmod_call = mock.call(
            [
                'chmod',
                'u+x',
                os.path.join(
                    ctx.instance.runtime_properties['root_directory'],
                    'serverless'
                )
            ],
            ctx.logger
        )
        run_sub_sdk.assert_has_calls([download_call, chmod_call])
