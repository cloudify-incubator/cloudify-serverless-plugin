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

from functools import wraps

from .utils import initialize_serverless, generate_traceback_exception

from cloudify.exceptions import NonRecoverableError


def with_serverless(func):
    @wraps(func)
    def function(*args, **kwargs):
        ctx = kwargs['ctx']
        kwargs['serverless'] = initialize_serverless(ctx)
        try:
            func(*args, **kwargs)
        except Exception as error:
            error_traceback = generate_traceback_exception()
            raise NonRecoverableError('{0}'.format(str(error)),
                                      causes=[error_traceback])
    return function
