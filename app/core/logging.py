import logging
from pythonjsonlogger import jsonlogger

def configure_logging(level: str = "INFO") -> None:
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    # Remove handlers to avoid duplicates
    for h in list(logger.handlers):
        logger.removeHandler(h)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
