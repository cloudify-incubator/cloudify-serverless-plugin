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
import yaml
import shutil
import logging
import unittest
from functools import wraps
from tempfile import mkdtemp

from mock import patch

from .. import Serverless

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


class ServerlessSDKTestBase(unittest.TestCase):

    @property
    def test_options(self):
        return [
            '--name',
            'bar',
            '--template',
            'baz',
            None,
            [
                {
                    'name': 'qux',
                    'handler': 'quux',
                    'events': ['bongo'],
                    'environment': {'taco': 'bell'}
                }
            ]
        ]

    def _test_wrapper(func):
        """Add handling for removing test dir and other common objs
        That should be recreated for every individual test.
        :return:
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['test_logger'] = logging.getLogger(__name__)
            kwargs['test_root_dir'] = mkdtemp()
            try:
                func(*args, **kwargs)
            finally:
                shutil.rmtree(kwargs['test_root_dir'])

        return wrapper

    @_test_wrapper
    def test_initialize_parameters(self,
                                   test_logger,
                                   test_root_dir,
                                   *_,
                                   **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )
        self.assertEqual(
            sl.logger,
            test_logger
        )
        self.assertEqual(
            sl.client_config,
            TEST_CLIENT_CONFIG
        )
        self.assertEqual(
            sl.resource_config,
            TEST_RESOURCE_CONFIG
        )
        self.assertEqual(
            sl.serverless_config,
            TEST_SERVERLESS_CONFIG
        )
        self.assertEqual(
            sl.root_directory,
            test_root_dir
        )
        self.assertEqual(
            sl.credentials_command,
            [
                'config',
                'credentials',
                '--provider',
                'foobar',
                '--key',
                'secret_name',
                '--secret',
                'super_secret'
            ]
        )
        self.assertEqual(
            sl.executable_path,
            'foo'
        )
        self.assertEqual(
            sl.options,
            [
                '--name',
                'bar',
                '--template',
                'baz',
                None,
                [
                    {
                        'name': 'qux',
                        'handler': 'quux',
                        'events': ['bongo'],
                        'environment': {'taco': 'bell'}
                    }
                ]
            ]
        )

    @_test_wrapper
    def test_command(self,
                     test_logger,
                     test_root_dir,
                     *_,
                     **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        self.assertEqual(
            sl._command(['bar']),
            ['foo', 'bar']
        )

    @_test_wrapper
    def test_subcommand(self,
                        test_logger,
                        test_root_dir,
                        *_,
                        **__):
        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )
        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl._subcommand('bar', ['--baz'], 'qux')
            run_subprocess.assert_called_with(
                ['foo', 'bar', '--baz'],
                sl.logger,
                'qux',
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_create(self,
                    test_logger,
                    test_root_dir,
                    *_,
                    **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl.create()
            cmd = ['foo', 'create']
            cmd.extend(self.test_options)
            run_subprocess.assert_called_with(
                cmd,
                sl.logger,
                sl.root_directory,
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_deploy(self,
                    test_logger,
                    test_root_dir,
                    *_,
                    **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl.deploy()
            cmd = ['foo', 'deploy']
            run_subprocess.assert_called_with(
                cmd,
                sl.logger,
                sl.root_directory,
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_destroy(self,
                     test_logger,
                     test_root_dir,
                     *_,
                     **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl.destroy()
            cmd = ['foo', 'remove']
            run_subprocess.assert_called_with(
                cmd,
                sl.logger,
                sl.root_directory,
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_configure(self,
                       test_logger,
                       test_root_dir,
                       *_,
                       **__):

        client_config = {
            'provider': 'aws',
            'credentials': {
                'key': 'secret_name',
                'secret': 'super_secret',
            }
        }
        sl = Serverless(
            test_logger,
            client_config,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )
        with open(os.path.join(test_root_dir, 'serverless.yml'), 'w') as fout:
            yaml.dump(TEST_RESOURCE_CONFIG, fout, allow_unicode=True)

        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl.configure()
            cmd = [
                'foo',
                'config',
                'credentials',
                '--provider',
                'aws',
                '--key',
                'secret_name',
                '--secret',
                'super_secret'
            ]
            run_subprocess.assert_called_with(
                cmd,
                sl.logger,
                sl.root_directory,
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_invoke(self,
                    test_logger,
                    test_root_dir,
                    *_,
                    **__):

        sl = Serverless(
            test_logger,
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.run_subprocess') as run_subprocess:
            run_subprocess.return_value = True
            sl.invoke('yum')
            cmd = ['foo', 'invoke', '--function', 'yum']
            run_subprocess.assert_called_with(
                cmd,
                sl.logger,
                sl.root_directory,
                None,
                {
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )
