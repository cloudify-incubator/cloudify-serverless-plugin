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

from cloudify_common_sdk.utils import get_node_instance_dir
from cloudify_common_sdk.secure_property_management import get_stored_property

from serverless_sdk import Serverless

SERVERLESS_PARAMS = [
    'serverless_config',
    'resource_config',
    'client_config',
]


def initialize_serverless(_ctx):
    params = {}
    for key in SERVERLESS_PARAMS:
        params[key] = get_stored_property(_ctx, key)
    params['root_directory'] = get_node_instance_dir()
    params['logger'] = _ctx.logger
    return Serverless(**params)
