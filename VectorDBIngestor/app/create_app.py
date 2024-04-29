from json import loads

from fastapi import FastAPI
import asyncio
from aiokafka import AIOKafkaConsumer
import logging
from app.config import get_config
from app.log_setup import setup_logging
from langchain_core.documents import Document
from app.utils.verify_kafka import check_kafka_connection
from langchain_openai import OpenAIEmbeddings
from  app.utils.get_qdrant import get_qdrant_vector_store

config = get_config()
app = FastAPI(
    title=get_config().TITLE,
    description=get_config().DESCRIPTION,
    debug=get_config().DEBUG
)
def setup_logging():
    logging.basicConfig(level=logging.INFO)

    # Optional: Implement retry logic here


async def consume_and_store_documents():
    config = get_config()
    consumer = AIOKafkaConsumer(
        config.VECTORDB_TOPIC_NAME,
        bootstrap_servers=config.KAFKA_SERVER,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group-id',
        value_deserializer=lambda x: loads(x.decode('utf-8'))
    )

    await consumer.start()
    logging.info("Kafka Consumer has started.")

    try:
        async for message in consumer:
            documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in message.value]
            for doc in documents:
                logging.info(doc.metadata)
            # Determine collection name dynamically from document metadata

            try:
                collection_name=documents[0].metadata['author']
                logging.info(f"collection is called {collection_name}")
                embed = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
                vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                                   embeddings=embed, collection_name=collection_name)
                ids = await vectordb.aadd_documents(documents)
                for id in ids:
                    logging.info(f"Document ID {id} added to collection")
                logging.info(f"Processed {len(ids)} documents into vectordb collection")
            except Exception as e:
                logging.error(f"Failed to connect to Qdrant: {e}")



    except Exception as e:
        logging.error(f"Error in consuming or storing documents: {e}")
    finally:
        await consumer.stop()
        logging.info("Kafka Consumer has closed.")


@app.on_event("startup")
async def startup_event():

    if await check_kafka_connection(config.KAFKA_SERVER, config.VECTORDB_TOPIC_NAME):  # Make sure this function is async
        logging.info("Starting up the consumer background task.")
        asyncio.create_task(consume_and_store_documents())
    else:
        logging.error("Kafka is not ready - consumer task will not start.")

@app.on_event("shutdown")
async def shutdown_event():
    # Handling of shutdown is typically managed via FastAPI's event lifecycle
    logging.info("Application shutdown initiated.")

@app.get("/")
async def read_root():
    return {"message": "Consumer is running in the background."}

def create_app():
    setup_logging()
    return app
