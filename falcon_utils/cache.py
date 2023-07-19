import inspect
import functools
import typing
import logging

logger = logging.get_logger(__name__)

try:
    import falcon_caching as caching
    import falcon_caching.middleware as caching_middleware
    
    @staticmethod
    def cached(timeout: int):
        """ This is the decorator used to decorate a resource class or the requested
        method of the resource class
        """
        def wrap1(class_or_method, *args):
            # is this about decorating a class or a given method?
            if inspect.isclass(class_or_method):
                # get all methods of the class that needs to be decorated (eg start with "on_"):
                for attr in dir(class_or_method):
                    if callable(getattr(class_or_method, attr)) and caching_middleware._DECORABLE_METHOD_NAME.match(attr):
                        setattr(class_or_method, attr, wrap1(getattr(class_or_method, attr)))

                return class_or_method
            else:  # this is to decorate the individual method
                class_or_method.to_be_cached = True

                @functools.wraps(class_or_method)
                def cache_wrap(cls, req, resp, *args, **kwargs):
                    class_or_method(cls, req, resp, *args, **kwargs)
                    req.context.cache = True
                    req.context.cache_timeout = timeout

                return cache_wrap

        # this is the name which will check for if the decorator was registered with the register()
        # function, as this decorator is not the topmost one
        wrap1._decorator_name = 'cache'  # type: ignore

        return wrap1


    @staticmethod
    def generate_cache_key(req, method: str = None) -> str:
        """ Generate the cache key from the request using the path and the method """
        path = req.path
        if path.endswith('/'):
            path = path[:-1]

        if not method:
            method = req.method

        param_keys = list(req.params.keys())
        param_keys.sort()
        query_keys = []

        for key in param_keys:
            value = ",".join(req.get_param_as_list(key))
            query_keys.append(f"{key}:{value}")
        query_keys = ":".join(query_keys)

        return f'{path}:{method.upper()}:{query_keys}'


    def get_default_redis_cache(
        host: "str" = "localhost",
        port: "int" = 6379,
        db: "int" = 0,
        password: "typing.Optional[str]" = None,
        key_prefix: "typing.Optional[str]" = None,
        redis_url: "typing.Optional[str]" = None,
    ):
        config={
            "CACHE_TYPE": "redis",
            "CACHE_EVICTION_STRATEGY": "time-based",
            "CACHE_KEY_PREFIX": key_prefix,
        }
        if redis_url:
            config.update({ 'CACHE_REDIS_URL': redis_url })
        else:
            config.update({ 
                "CACHE_REDIS_HOST": host,
                "CACHE_REDIS_PORT": port,
                "CACHE_REDIS_PASSWORD": password,
                "CACHE_REDIS_DB": db
            })
        return caching.Cache(config=config)

    caching.Cache.cached = cached
    caching_middleware.Middleware.generate_cache_key = generate_cache_key
except ImportError as e:
    logger.warn("Falcon Caching is not installed")
    logger.warn("Impelementing stubs")
    cached = None
    get_default_redis_cache = None
    generate_cache_key = None


# from falcon_caching import Cache, middleware
# from falcon_caching.middleware import _DECORABLE_METHOD_NAME


