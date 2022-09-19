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

EXPECTED_SERVERLESS_YML = """functions:
- qux:
    environment:
      taco: bell
    events:
    - bongo
    handler: quux
name: bar
template: baz
template_path: ''
template_url: ''
"""

FOO_YAML = """service: aws-service
stage: dev
region: us-east-1
stack: aws-service-dev
functions:
  hello_1: aws-service-dev-hello_1
  hello_2: aws-service-dev-hello_2
"""

FOO_JSON = {
    'service': 'aws-service',
    'stage': 'dev',
    'region': 'us-east-1',
    'stack': 'aws-service-dev',
    'functions': {
        'hello_1': 'aws-service-dev-hello_1',
        'hello_2': 'aws-service-dev-hello_2'
    }
}


class ServerlessSDKTestBase(unittest.TestCase):

    @property
    def test_options(self):
        return [
            '--name',
            'bar',
            '--template',
            'baz',
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
            'test_dp',
            'test_ni',
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
            sl.executable_path,
            'foo'
        )
        self.assertEqual(
            sl.options,
            ['--name', 'bar', '--template', 'baz']
        )

    @_test_wrapper
    def test_command(self,
                     test_logger,
                     test_root_dir,
                     *_,
                     **__):

        sl = Serverless(
            test_logger,
            'test_dp',
            'test_ni',
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
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )
        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl._subcommand('bar', ['--baz'], 'qux')
            run_subprocess.assert_called_with(
                ['foo', 'bar', '--baz'],
                'qux',
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
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
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.create()
            cmd = ['foo', 'create', '--name', 'bar', '--template', 'baz']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
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
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.deploy()
            cmd = ['foo', 'deploy']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
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
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.destroy()
            cmd = ['foo', 'remove']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
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
            'test_dp',
            'test_ni',
            client_config,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )
        with open(os.path.join(test_root_dir, 'serverless.yml'), 'w') as fout:
            yaml.dump(TEST_RESOURCE_CONFIG, fout, allow_unicode=True)

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.configure()
            with open(os.path.join(test_root_dir, 'serverless.yml'),
                      'r') as fout:
                self.assertEqual(fout.read(), EXPECTED_SERVERLESS_YML)

    @_test_wrapper
    def test_invoke(self,
                    test_logger,
                    test_root_dir,
                    *_,
                    **__):

        sl = Serverless(
            test_logger,
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.invoke('yum')
            cmd = ['foo', 'invoke', '--function', 'yum']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_metrics(self,
                     test_logger,
                     test_root_dir,
                     *_,
                     **__):

        sl = Serverless(
            test_logger,
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = True
            sl.metrics('yum')
            cmd = ['foo', 'metrics', '--function', 'yum']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )

    @_test_wrapper
    def test_info(self,
                  test_logger,
                  test_root_dir,
                  *_,
                  **__):

        sl = Serverless(
            test_logger,
            'test_dp',
            'test_ni',
            TEST_CLIENT_CONFIG,
            TEST_RESOURCE_CONFIG,
            TEST_SERVERLESS_CONFIG,
            test_root_dir,
        )

        with patch('serverless_sdk.Serverless._execute') as run_subprocess:
            run_subprocess.return_value = FOO_YAML
            result = sl.info()
            cmd = ['foo', 'info']
            run_subprocess.assert_called_with(
                cmd,
                sl.root_directory,
                {
                    'TMP': sl.tempenv,
                    'TEMP': sl.tempenv,
                    'TMPDIR': sl.tempenv,
                },
                additional_args={
                    'env': {},
                    'log_stdout': sl._log_stdout
                },
                return_output=sl._log_stdout
            )
            self.assertEqual(result, FOO_JSON)
