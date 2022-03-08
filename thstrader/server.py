import logging
from thstrader.apps.handler import app

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
