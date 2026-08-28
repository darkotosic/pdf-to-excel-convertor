import logging
from logging.handlers import RotatingFileHandler
from platformdirs import user_log_path


def configure_logging() -> None:
    path = user_log_path("pdf-to-excel-converter")
    path.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        path / "application.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[handler],
    )
