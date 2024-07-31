import logging
import logging.config
import os

# 确保日志目录存在
log_dir = "./.log"
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录器
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(log_dir, "biotree.log"),
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "biotree": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)


# 在顶层模块中获取日志记录器
logger = logging.getLogger("biotree")
logger.info("Logging for biotree module")
