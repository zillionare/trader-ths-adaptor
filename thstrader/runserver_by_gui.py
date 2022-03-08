# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-01-26 14:31
import logging
from threading import Thread
import sys

setattr(sys, "gui", True)
from thstrader.gui import gui_app  # noqa
from thstrader.server import app  # noqa

logger = logging.getLogger(__name__)


def start_server(port=1430):
    t = Thread(target=app.run, daemon=True, kwargs={"host": "0.0.0.0", "port": port})
    t.start()


if __name__ == "__main__":
    start_server()
    gui_app.mainloop()