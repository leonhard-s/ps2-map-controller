"""Custom logging behaviour for the API server."""

import copy
import logging
from typing import Any


class ForwardHandler(logging.Handler):
    """A custom logging handler that forwards log messages.

    This forwards any log records passed to the logger passed in its
    initialiser.
    The re-emitted log records will be modified to use the name of the
    handler's logger, rather than the handler being forwarded.

    This renaming alters the original log record. You can set the
    `copy_records` kwarg in the handler's initialiser to `False` to
    keep create a deepcopy of the record prior to renaming.
    """

    def __init__(self, logger: logging.Logger, *args: Any,
                 copy_records: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__copy_records = copy_records
        self.__logger = logger

    def emit(self, record: logging.LogRecord) -> None:
        if self.__copy_records:
            record = copy.deepcopy(record)
        record.name = self.__logger.name
        self.__logger.handle(record)
