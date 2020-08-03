
import logging
import logging.config


def setup_logger(name, token, console_level, external_level):
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': console_level,
            'formatter': 'standard'
        }
    }

    loggers = {
        name: {
            'handlers': ['console'],
            'propagate': True
        }
    }

    if token:
        handlers['LogzioHandler'] = {
            'formatter': 'standard',
            'class': 'logzio.handler.LogzioHandler',
            'token': token,
            'logzio_type': name,
            'level': external_level
        }
        loggers[name]['handlers'].append('LogzioHandler')

    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': (
                        '%(asctime)s [%(levelname)s] '
                        '%(name)s: %(message)s'
                    )
                }
            },
            'handlers': handlers,
            'loggers': loggers,
            'level': 'DEBUG',
        }
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    return logger
