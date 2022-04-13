import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from thstrader.apps.routers import app

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1430)
