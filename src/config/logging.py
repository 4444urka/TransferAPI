LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'monitoring': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        # Добавьте этот блок
        'utils': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Уровень DEBUG для отображения всех сообщений
            'propagate': True,
        },
    },
}