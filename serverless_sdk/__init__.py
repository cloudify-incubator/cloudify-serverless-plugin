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


class CloudifyServerlessSDKError(Exception):
    pass


class Serverless(object):
    """
    This is an interface for handling running and configuring
    Serverless in different providers
    """

    def __init__(self,
                 logger,
                 provider_config,
                 service_path,
                 executable_path=None,
                 functions=None,
                 variables=None):
        self.logger = logger
        self.service_path = service_path
        self.provider_config = provider_config
        self.executable_path = executable_path or 'serverless'
        self.functions = functions
        self.variables = variables

    def init(self):
        pass

    def deploy(self):
        pass

    def configure(self):
        pass

    def destroy(self):
        pass

    def execute(self, command):
        pass
