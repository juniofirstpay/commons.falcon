import structlog
import os
import traceback
import typing

logger = structlog.get_logger(__name__)

try:
    import newrelic.agent
except ImportError as e:
    logger.warn("NewRelic Agent is not installed")


DEFAULT_FILE_PATH = os.path.join(os.getcwd(), "./new-relic.ini")


def setup_new_relic(
    environment: str, app: "falcon.App", file_path: "typing.Optional[str]" = None
):
    try:
        newrelic.agent.initialize(
            file_path or DEFAULT_FILE_PATH, environment=environment
        )
        return newrelic.agent.WSGIApplicationWrapper(app)
    except Exception as e:
        traceback.print_exc()
    return app
