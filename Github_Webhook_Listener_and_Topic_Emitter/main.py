

import uvicorn


from  app.config import get_config

from  app.create_app import create_app

config = get_config()
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)