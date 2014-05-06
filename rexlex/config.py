import logging


LOG_MSG_MAXWIDTH = 1000

# ---------------------------------------------------------------------------
# Configure logging module.
# ---------------------------------------------------------------------------
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s %(levelname)s %(name)s: %(message)s",
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'default': {'level': 'REXLEX_TRACE',
                    'class': 'rexlex.log_config.ColorizingStreamHandler',
                    'formatter': 'standard'},
    },
    'loggers': {
        'rexlex': {
            'handlers': ['default'], 'level': 'REXLEX_TRACE', 'propagate': False
        },
    },
}