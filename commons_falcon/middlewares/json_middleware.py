import json
import re
import falcon
import six
import logging
from datetime import datetime


logger = logging.getLogger(__name__)

bs = None
try:
    import bson.json_utils as bs
except ImportError as e:
    logger.error(e)

if bs is None:
    try:
        import bson as bs
    except ImportError as e:
        logger.error(e)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class JsonMiddleware(object):
    def __init__(self, help_messages=True):
        """help_messages: display validation/error messages"""
        self.debug = bool(help_messages)

    def bad_request(self, title, description):
        """Shortcut to respond with 400 Bad Request"""
        if self.debug:
            raise falcon.HTTPBadRequest(title, description)
        else:
            raise falcon.HTTPBadRequest()

    def get_json(self, field, **kwargs):
        """Helper to access JSON fields in the request body

        Optional built-in validators.
        """
        value = None
        if field in self.req.json:
            value = self.req.json[field]
            kwargs.pop("default", None)
        elif "default" not in kwargs:
            self.bad_request(
                "Missing JSON field", "Field '{}' is required".format(field)
            )
        else:
            value = kwargs.pop("default")
        validators = kwargs
        return self.validate(field, value, **validators)

    def validate(
        self,
        field,
        value,
        dtype=None,
        default=None,
        min=None,
        max=None,
        match=None,
        choices=None,
    ):
        """JSON field validators:

        dtype      data type
        default    value used if field is not provided in the request body
        min        minimum length (str) or value (int, float)
        max        maximum length (str) or value (int, float)
        match      regular expression
        choices    list to which the value should be limited
        """
        err_title = "Validation error"

        if dtype:
            if dtype == str and type(value) in six.string_types:
                pass

            elif type(value) is not dtype:
                msg = "Data type for '{}' is '{}' but should be '{}'"
                self.bad_request(
                    err_title, msg.format(field, 
                                          type(value).__name__, 
                                          dtype.__name__)
                )

        if type(value) in six.string_types:
            if min and len(value) < min:
                self.bad_request(
                    err_title, "Minimum length for '{}' is '{}'".format(field, min)
                )

            if max and len(value) > max:
                self.bad_request(
                    err_title, "Maximum length for '{}' is '{}'".format(field, max)
                )

        elif type(value) in (int, float):
            if min and value < min:
                self.bad_request(
                    err_title, "Minimum value for '{}' is '{}'".format(field, min)
                )

            if max and value > max:
                self.bad_request(
                    err_title, "Maximum value for '{}' is '{}'".format(field, max)
                )

        if match and not re.match(match, re.escape(value)):
            self.bad_request(
                err_title, "'{}' does not match Regex: {}".format(field, match)
            )

        if choices and value not in choices:
            self.bad_request(err_title, "{} must be one of {}".format(field, choices))
        return value

    def process_request(self, req: "falcon.Request", resp):
        """Middleware request"""

        if (
            getattr(req, "content_type", None)
            and "multipart/form-data" in req.content_type
        ):
            return

        if not getattr(req, "content_length", None):
            return

        body = req.stream.read()
        req.json = {}
        self.req = req
        req.get_json = self.get_json  # helper function
        try:
            req.json = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError:
            self.bad_request("Invalid encoding", "Could not decode as UTF-8")
        except ValueError:
            self.bad_request("Malformed JSON", "Syntax error")

    def process_response(self, req, resp, resource, req_succeeded):
        """Middleware response"""
        if getattr(resp, "json", None) is not None:
            resp.body = str.encode(bs.dumps(resp.json))
