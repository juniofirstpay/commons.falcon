import enum
import json
import typing
import datetime
import functools
import logging

logger = logging.getLogger(__name__)


try:
    import requests
except ImportError as e:
    logger.warn("requests module not found")

try:
    import jwcrypto.jwt as jwt
    import jwcrypto.jwk as jwk
    import jwcrypto.common as jwt_commons
except ImportError as e:
    logger.warn("jwtcrypto module not found")



__all__ = ('AuthorizationScheme', 'AccessLevel', 'JWTVerificationError', 'timed_lru_cache', 'JWTVerifyService',)

class AuthorizationScheme(enum.Enum):
    JWT = "jwt"
    EXEMPTED_PATH = "exempted_path"
    IP_WHITELIST = "ip_whitelist"
    API_KEY = "api_key"
    CLIENT_SECRET = "client_secret"
    ACCESS_TOKEN = "access_token"


class AccessLevel(enum.Enum):
    SELF = "self"
    DEPENDANT = "dependant"
    SELF_AND_DEPENDANT = "self_and_dependant"


class JWTVerificationError(enum.Enum):
    EXPIRED = "expired"
    INVALID = "invalid"
    INTERNAL = "internal"


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = functools.lru_cache(maxsize=maxsize)(func)
        func.lifetime = datetime.timedelta(seconds=seconds)
        func.expiration = datetime.datetime.utcnow() + func.lifetime

        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.datetime.utcnow() + func.lifetime

            result = func(*args, **kwargs)
            return result

        return wrapped_func

    return wrapper_cache


class JWTVerifyService:
    def __init__(self, url: str) -> None:
        self.service_url = url

    @timed_lru_cache(3600)
    def fetch_jwk(self):
        headers = {"X-Api-Version": "v1"}
        response = requests.get(self.service_url, headers=headers)
        if response.status_code != 200:
            return None

        return response.json()

    def verify(self, token: str) -> "typing.Union[tuple[JWTVerificationError, None], tuple[None, str]]":
        try:
            jwk_api_response = self.fetch_jwk()
            if not jwk_api_response:
                return JWTVerificationError.INTERNAL, None

            jwk_set = jwk.JWKSet.from_json(json.dumps(jwk_api_response))
            decoded_token = jwt.JWT(key=jwk_set, jwt=token)
            claims = json.loads(decoded_token.claims)

            return None, claims
        except (jwt_commons.JWException, ValueError) as error:
            if isinstance(error, jwt.JWTExpired):
                return JWTVerificationError.EXPIRED, None
            
            return JWTVerificationError.INVALID, None


