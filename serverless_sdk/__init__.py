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
import subprocess

import yaml

from utils import CapturingOutputConsumer, LoggingOutputConsumer


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
                 provider_config,
                 service_config,
                 functions,
                 executable_path=None,
                 variables=None):
        self.logger = logger
        self.provider_config = provider_config
        self.service_config = service_config
        self.functions = functions
        self.executable_path = executable_path
        self.variables = variables
        self.root_directory = '/tmp'

    @property
    def provider(self):
        return self.provider_config.get('provider')

    @property
    def credentials(self):
        return self.provider_config.get('config')

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
    def credentials_dir(self):
        return os.path.join(os.path.expanduser('~'), '.aws')

    @property
    def serverless_base_dir(self):
        return os.path.join(
            self.root_directory,
            self.serverless_path,
        )

    @property
    def serverless_config_path(self):
        return os.path.join(self.serverless_base_dir, 'serverless.yml')

    @property
    def serverless_path(self):
        return self.service_config.get('path')

    @property
    def service_config_options(self):
        options = []
        for key, value in self.service_config.items():
            if value:
                option = SERVICE_CONFIG_MAP.get(key)
                options.append(option)
                options.append(value)
        return options

    def _serverless_command(self, command):
        exe_cmd = [self.executable_path]
        exe_cmd.extend(command)
        return exe_cmd

    def _action_command(self, action, options=[], cwd=None):
        cmd = [action]
        if options:
            cmd.extend(options)
        cmd = self._serverless_command(cmd)
        return self.execute(cmd, cwd=cwd)

    def create(self):
        return self._action_command('create', self.service_config_options)

    def configure(self):
        if self.provider == 'aws':
            cmd = self._serverless_command(self.credentials_command)
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

    def deploy(self):
        return self._action_command('deploy', cwd=self.serverless_base_dir)

    def destroy(self):
        return self._action_command('remove', cwd=self.serverless_base_dir)

    def clean(self):
        self.execute(['rm', '-rf', self.service_config.get('path')])
        self.execute(['rm', '-rf', self.credentials_dir])

    def execute(self, command, return_output=False, cwd=None):
        if not cwd:
            cwd = self.root_directory
        self.logger.info(
            "Running: %s, working directory: %s", command, cwd
        )

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=None,
            cwd=cwd
        )

        if return_output:
            stdout_consumer = CapturingOutputConsumer(
                process.stdout)
        else:
            stdout_consumer = LoggingOutputConsumer(
                process.stdout, self.logger, "<out> ")
        stderr_consumer = LoggingOutputConsumer(
            process.stderr, self.logger, "<err> ")

        return_code = process.wait()
        stdout_consumer.join()
        stderr_consumer.join()

        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

        output = stdout_consumer.buffer.getvalue() if return_output else None
        self.logger.info(
            "Returning output:\n%s", output if output is not None else '<None>'
        )
        return output
