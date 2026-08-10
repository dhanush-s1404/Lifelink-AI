"""Structured logging via structlog.

Sensitive values (passwords, tokens, keys, vault content) must never be passed to the logger.
"""

import logging

import structlog

_SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie"}


def _drop_sensitive(_logger, _method_name, event_dict):
    if isinstance(event_dict, dict):
        for key in list(event_dict.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _drop_sensitive,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=level)


logger = structlog.get_logger()
