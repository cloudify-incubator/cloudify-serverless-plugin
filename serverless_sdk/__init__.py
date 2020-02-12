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

import subprocess

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
    def credentials(self):
        return self.provider_config.get('config')

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

    def create(self):
        cmd = ['create']
        cmd.extend(self.service_config_options)
        cmd = self._serverless_command(cmd)
        return self.execute(cmd)

    def configure(self):
        pass

    def install(self):
        pass

    def deploy(self):
        pass

    def destroy(self):
        pass

    def clean(self):
        self.execute(['rm', '-rf', self.service_config.get('path')])

    def execute(self, command, return_output=False):
        additional_args = {}
        self.logger.info(
            "Running: %s, working directory: %s", command, self.root_directory
        )

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=None,
            cwd=self.root_directory,
            **additional_args)

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
