import logging

from fastapi import Depends, FastAPI

from  app import routes


def create_app():
    """
    Create a FastAPI application
    """

    # Fetch configurations from the environment


    # Create FastAPI app instance with provided configurations
    app = FastAPI(
        title="Github_Webhook_Listener_and_Topic_Emitter",
        description="""This microservice serves as an entry point for GitHub webhook events. It has two primary functions:
Webhook Receiver Endpoint: Listens for new commits on specified repositories and emits these commit details to designated Kafka topics.
Repository Setter Endpoint: Accepts a repository name from the user, sets or switches the current repository being monitored, and can emit this configuration change to a Kafka topic if needed.""",
        debug=True,

    )

    # Add middleware

    app.include_router(routes.router)

    # Add database connection
    @app.on_event("startup")
    def startup():
        pass

    @app.on_event("shutdown")
    async def shutdown():
        pass

    # Root endpoint
    @app.get("/")
    async def root():
        """
        Root endpoint
        """

        logging.info("Root endpoint")
        return {"message": "Hello World"}

    return app