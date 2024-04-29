import uvicorn

from app.log_setup import setup_logging
from app.config import get_config
from app.create_app import create_app

setup_logging()  # Ensure logging is configured before the app starts

config = get_config()
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
