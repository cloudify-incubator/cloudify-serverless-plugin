
from cloudify.decorators import operation

from decorators import with_serverless


@operation
@with_serverless
def create(ctx, serverless, **_):
    pass


@operation
@with_serverless
def configure(ctx, serverless, **_):
    pass


@operation
@with_serverless
def start(ctx, serverless, **_):
    pass


@operation
@with_serverless
def delete(ctx, serverless, **_):
    pass
