import enum
import typing
import structlog
import commons_falcon.errors as errors

logger = structlog.get_logger(__name__)

try:
    import falcon
except ImportError as e:
    logger.warn("falcon module not found")

try:
    import limits
except ImportError as e:
    logger.warn("limits module not found")
    

class RateLimitingMiddleware:
    
    class Type(enum.Enum):
        FIXED_WINDOW = 1
        ELASTIC_WINDOW = 2
        MOVING_WINDOW = 3
    
    def __init__(self, config: "type.Dict"):
        self.__limiters = {}
        self.__config = config
        if self.__config.get('url'):
            self.__storage = limits.storage.RedisStorage(self.__config['url'])
        elif self.__config.get('password'):
            self.__storage = limits.storage.RedisStorage(f"redis://{self.__config['username']}:{self.__config['password']}@{self.__config['host']}:{self.__config['port']}")
        else:
            self.__storage = limits.storage.RedisStorage(f"redis://{self.__config['host']}:{self.__config['port']}")
        if self.__config["type"] == self.Type.FIXED_WINDOW:
            self.__strategy = limits.strategies.FixedWindowRateLimiter(self.__storage)
        elif self.__config["type"] == self.Type.ELASTIC_WINDOW:
            self.__strategy = limits.strategies.FixedWindowElasticExpiryRateLimiter(self.__storage)
        elif self.__config["type"] == self.Type.MOVING_WINDOW:
            self.__strategy = limits.strategies.MovingWindowRateLimiter(self.__storage)
    
    @property
    def middleware(self):
        return self
    
    def process_resource(self, req:"falcon.Request", resp: "falcon.Response", resource, params):
        namespace = f"{resource.__class__.__name__}.on_{req.method.lower()}"
        limiters = self.__limiters.get(namespace)
        if limiters is not None and isinstance(limiters, list):
            blocking_limit_item = next(filter(lambda limit_item: self.__strategy.hit(limit_item, req.path, req.method) == False, limiters), None)
            if blocking_limit_item is not None:
                resp.complete = True
                reset_time, _ = self.__strategy.get_window_stats(blocking_limit_item, req.path, req.method)
                resp.append_header('X-Rate-Limit-ResetTime',reset_time)
                raise errors.RateLimitError()
    
    def apply_limits(self, limiters: "typing.List[str]"):
        
        def hook_func(func):
            namespace = f"{func.__qualname__}"
            self.__limiters[namespace] = list(map(lambda x: limits.parse(x), limiters))
            return func
            
        return hook_func

