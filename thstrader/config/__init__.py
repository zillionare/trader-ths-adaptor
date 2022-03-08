# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-01-25 15:31

import os

from logging.config import dictConfig

import cfg4py as cfg4py

from thstrader.config.schema import Config
from thstrader.utils import BASE_DIR
import logging.config
import sys
from os import path
from flask import Flask

gui = getattr(sys, "gui", False)
LOG_PATH = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_PATH, "easytrader_server.log")
LOG_LEVEL = logging.DEBUG
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


def get_config_dir():
    # server_role = os.environ.get(cfg4py.envar)

    # if server_role == "DEV":
    _dir = path.dirname(__file__)
    # elif server_role == "TEST":
    #     _dir = path.expanduser("~/.zillionare/omega/config")
    # else:
    #     _dir = path.expanduser("~/zillionare/omega/config")
    #
    sys.path.insert(0, _dir)
    return _dir


cfg4py.init(get_config_dir(), False)

cfg: Config = cfg4py.get_instance()

log_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": cfg.log_level,
            "formatter": "default",
        },
        "file": {
            "level": cfg.log_level,
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "encoding": "utf8",
            "formatter": "default",
        },
    },
    "loggers": {
        "thstrader": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        }
    },
}

if gui:
    log_dict["handlers"]["gui"] = {
        "class": "thstrader.gui.MyLogHandler",
        "formatter": "default",
        # 注意，class，formatter，level，filters之外的参数将默认传递给由class指定类的构造函数
        "name": "LoggerHandler",
    }
    for i, value in log_dict["loggers"].items():
        value["handlers"].append("gui")

dictConfig(log_dict)
logger = logging.getLogger(__name__)

logger.info("BASE_DIR:" + BASE_DIR)
app = Flask("traderserver")
