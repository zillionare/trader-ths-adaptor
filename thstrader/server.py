import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from thstrader.apps.routers import app
from thstrader.apps.handler import start_executor_action, TimedQueryEntrust

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    start_executor_action()
    TimedQueryEntrust.run()
    app.run(host="0.0.0.0")
