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
import tempfile
from pathlib import Path

import yaml
from cloudify_common_sdk.cli_tool_base import CliTool


class CloudifyServerlessSDKError(Exception):
    pass


SERVICE_CONFIG_MAP = {
    'name': '--name',
    'template': '--template',
    'template_url': '--template-url',
    'template_path': '--template-path',
    'path': '--path'
}


class Serverless(CliTool):
    """
    This is an interface for handling running and configuring
    Serverless in different providers
    """

    def __init__(self,
                 logger,
                 deployment_name,
                 node_instance_name,
                 client_config=None,
                 resource_config=None,
                 serverless_config=None,
                 root_directory=None,
                 ):

        self._tool_name = 'serverless'
        super().__init__(logger, deployment_name, node_instance_name)
        self._client_config = client_config or {}
        self._resource_config = resource_config or {}
        self._serverless_config = serverless_config or {}
        self._root_directory = root_directory
        self._serverless_config_path = None
        self._additional_args = {
            'env': {}
        }
        self._tempenv = None
        self._log_stdout = True

    @property
    def additional_args(self):
        return self._additional_args

    @property
    def client_config(self):
        return self._client_config

    @property
    def resource_config(self):
        return self._resource_config

    @property
    def serverless_config(self):
        return self._serverless_config

    @property
    def root_directory(self):
        return self._root_directory

    @additional_args.setter
    def additional_args(self, value):
        self._additional_args = value

    @client_config.setter
    def client_config(self, value):
        self._client_config = value

    @resource_config.setter
    def resource_config(self, value):
        self._resource_config = value

    @serverless_config.setter
    def serverless_config(self, value):
        self._serverless_config = value

    @root_directory.setter
    def root_directory(self, value):
        self._root_directory = value

    @property
    def provider(self):
        return self.client_config.get('provider')

    @property
    def credentials(self):
        return self.client_config.get('credentials')

    @property
    def functions(self):
        return self.resource_config.get('functions')

    @property
    def serverless_config_path(self):
        if not self._serverless_config_path:
            self._serverless_config_path = os.path.join(
                self.root_directory, 'serverless.yml')
        return self._serverless_config_path

    @serverless_config_path.setter
    def serverless_config_path(self, value):
        self._serverless_config_path = value

    @property
    def tempenv(self):
        if not self._tempenv:
            self._tempenv = tempfile.mkdtemp()
        return self._tempenv

    @property
    def executable_path(self):
        if not self._executable_path:
            self._executable_path = self.serverless_config.get(
                'executable_path')
        return self._executable_path

    @executable_path.setter
    def executable_path(self, value):
        self._executable_path = value

    @property
    def options(self):
        options = []
        for key, value in self.resource_config.items():
            if value:
                if key not in SERVICE_CONFIG_MAP:
                    self.logger.error(
                        'Resource config key {} is not valid. '
                        'Ignoring...'.format(key))
                    continue
                option = SERVICE_CONFIG_MAP.get(key)
                options.append(option)
                options.append(value)
        return options

    def _command(self, command):
        if not isinstance(command, list):
            raise ValueError(
                'Improper parameter command "{}", '
                'value should be a list, it is a {}'.format(
                    command, type(command)))
        exe_cmd = [self.executable_path]
        exe_cmd.extend(command)
        return exe_cmd

    def _subcommand(self, subcommand, options=None, cwd=None):
        options = options or []
        cmd = [subcommand]
        if options:
            cmd.extend(options)
        cmd = self._command(cmd)
        return self.execute(cmd, cwd=cwd)

    @property
    def create_options(self):
        options = []
        for key, value in self.resource_config.items():
            if key in ['functions', 'env']:
                continue
            if value:
                option = SERVICE_CONFIG_MAP.get(key)
                options.append(option)
                options.append(value)
                if option == 'name':
                    options.append(['--path', value])
        return options

    def create(self):
        return self._subcommand('create', self.create_options)

    def aws_warn(self):
        if self.provider == 'aws':
            self.logger.info('Provider "aws" was provided. '
                             'The default behavior for serverless is to '
                             'modify the ~/.aws profiles. However, since '
                             'Cloudify is a shared system, this is not '
                             'possible. The key and secret that were provided '
                             'will be used in environment variables.')

    def configure(self):
        self.aws_warn()
        if not os.path.exists(self.serverless_config_path):
            Path(self.serverless_config_path).touch()
        with open(self.serverless_config_path, 'r') as yaml_file:
            serverless_config = yaml_file.read()
        config = yaml.safe_load(serverless_config) or {}
        functions = []
        # Handling functions configurations
        for function in self.functions:
            function_name = function['name']
            fn_config = {
                key: value for key, value in function.items()
                if key not in ['path', 'name']
            }
            functions.append({function_name: fn_config})
        config['functions'] = functions
        with open(self.serverless_config_path, 'w') as updated_file:
            yaml.safe_dump(config, updated_file, default_flow_style=False)

    def info(self):
        return yaml.safe_load(
            self._subcommand('info', cwd=self.root_directory))

    def invoke(self, name):
        return self._subcommand(
            'invoke',
            options=[
                '--function',
                name
            ],
            cwd=self.root_directory)

    def metrics(self, function_name=None):
        if function_name:
            options = ['--function', function_name]
        else:
            options = []
        return self._subcommand(
            'metrics',
            options=options,
            cwd=self.root_directory)

    def deploy(self):
        return self._subcommand('deploy', cwd=self.root_directory)

    def destroy(self):
        return self._subcommand('remove', cwd=self.root_directory)

    def clean(self):
        # TODO: I'm not sure if we want to be responsible here
        #  for removing files. although that could be a good idea.
        # self.execute(['rm', '-rf', self.resource_config.get('path')])
        # TODO: Delete credentials dir for example .aws, .kube, etc.
        # self.execute(['rm', '-rf', self.credentials_dir])
        pass

    def credentialize_env(self, env=None):
        env = env or {}
        env.update({
            'TMP': self.tempenv,
            'TEMP': self.tempenv,
            'TMPDIR': self.tempenv,
        })
        if self.client_config.get('provider') == 'aws':
            access_key = self.client_config.get(
                'credentials', {}).get('key')
            secret_key = self.client_config.get(
                'credentials', {}).get('secret')
            env.update(
                {
                    'AWS_ACCESS_KEY_ID': access_key,
                    'AWS_SECRET_ACCESS_KEY': secret_key
                }
            )
        env_from_props = self.resource_config.get('env')
        if env_from_props:
            for k, v in env_from_props.items():
                if k in env:
                    self.logger.error(
                        'The environment variable key {} is provided in the '
                        'resource config. However, it already exists in the '
                        'current shell. '
                        'This may have unexpected results.'.format(k))
                env[k] = v
        return env

    def execute(self,
                command,
                return_output=None,
                cwd=None,
                additional_env=None
                ):
        return_output = return_output if return_output is not None \
            else self._log_stdout
        self.additional_args['log_stdout'] = return_output
        try:
            result = self._execute(
                command,
                cwd or self.root_directory,
                env=self.credentialize_env(additional_env),
                additional_args=self.additional_args,
                return_output=return_output)
        finally:
            shutil.rmtree(self.tempenv, ignore_errors=True)
        return result

    def install_with_npm(self):
        command = 'npm install --prefix {} -g serverless'.format(
            self.root_directory)
        self.execute(
            command.split(),
            cwd=self.root_directory)
        self.executable_path = os.path.join(
            self.root_directory,
            'bin',
            'serverless'
        )

    def uninstall_with_npm(self):
        command = 'npm uninstall --prefix {} -g serverless'.format(
            self.root_directory)
        self.execute(
            command.split(),
            cwd=self.root_directory)
