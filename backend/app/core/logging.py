import logging
from app.core.config import get_settings

# added minimal logging to track what's going on in our docker containers
# docker container will be build later
def configure_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
    )
