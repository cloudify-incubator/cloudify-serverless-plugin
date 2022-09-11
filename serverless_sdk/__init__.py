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
from cloudify_common_sdk.utils import run_subprocess


class CloudifyServerlessSDKError(Exception):
    pass


SERVICE_CONFIG_MAP = {
    'name': '--name',
    'template': '--template',
    'template_url': '--template-url',
    'template_path': '--template-path',
    'path': '--path'
}


class Serverless(object):
    """
    This is an interface for handling running and configuring
    Serverless in different providers
    """

    def __init__(self,
                 logger,
                 client_config,
                 resource_config,
                 serverless_config=None,
                 root_directory=None,
                 ):

        self.logger = logger
        self._client_config = client_config
        self._resource_config = resource_config
        self._serverless_config = serverless_config
        self._root_directory = root_directory
        self._serverless_config_path = None
        self._additional_args = {}
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
            return os.path.join(self.root_directory, 'serverless.yml')
        return self._serverless_config_path

    @serverless_config_path.setter
    def serverless_config_path(self, value):
        self._serverless_config_path = value

    @property
    def credentials_command(self):
        return [
            'config',
            'credentials',
            '--provider',
            self.provider,
            '--key',
            self.credentials.get('key'),
            '--secret',
            self.credentials.get('secret')
        ]

    @property
    def executable_path(self):
        return self.serverless_config.get('executable_path')

    @property
    def options(self):
        options = []
        for key, value in self.resource_config.items():
            if value:
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

    def create(self):
        return self._subcommand('create', self.options)

    def configure(self):
        if self.provider == 'aws':
            cmd = self._command(self.credentials_command)
            self.execute(cmd)

        # TODO, need to handle other providers
        with open(self.serverless_config_path, 'r') as yaml_file:
            serverless_config = yaml_file.read()
        config = yaml.safe_load(serverless_config)
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

    def invoke(self, name):
        return self._subcommand(
            'invoke',
            options=[
                '--function',
                name
            ],
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

    def execute(self,
                command,
                return_output=None,
                cwd=None,
                additional_env=None
                ):
        return_output = return_output if return_output is not None \
            else self._log_stdout
        self.additional_args['log_stdout'] = return_output
        return run_subprocess(
            command,
            self.logger,
            cwd or self.root_directory,
            additional_env,
            self.additional_args,
            return_output=return_output)
