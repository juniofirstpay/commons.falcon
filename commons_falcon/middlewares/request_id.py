import typing
import secrets
from datetime import datetime

__all__ = ('FALCON_HEADER_REQUEST_ID', 'configure_falcon_request_id_middleware', 'generate_request_id')

FALCON_HEADER_REQUEST_ID = 'x-request-id'

def generate_request_id():
    return "{}.{}".format(datetime.utcnow().timestamp(), secrets.token_bytes(16).hex())

def configure_falcon_request_id_middleware():
    import falcon
    
    class FalconRequestIdMiddleware():
        
        def __init__(self, ctx: "dict" = None):
            self.__ctx = ctx # context from threading.local()

        def process_request(self, req: "falcon.Request", resp: "falcon.Response", *args, **kwargs):
            request_id: typing.Optional[str] = req.headers.get(FALCON_HEADER_REQUEST_ID)

            if request_id is None:
                request_id = generate_request_id()
            
            req.context['request_id'] = request_id
            if self.__ctx is not None:
                self.__ctx.request_id = request_id

    return FalconRequestIdMiddleware