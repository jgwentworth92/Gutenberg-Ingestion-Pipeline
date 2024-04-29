from json import loads

from fastapi import FastAPI
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import logging

from app.utils.process_message import process_message
from app.utils.setup_chat_model import setup_chat_model
from app.config import get_config
from app.log_setup import setup_logging

from app.utils.verify_kafka import check_kafka_connection

from app.utils.process_message import custom_serializer

config = get_config()
app = FastAPI(
    title=config.TITLE,
    description=config.DESCRIPTION,
    debug=config.DEBUG
)


def setup_logging():
    logging.basicConfig(level=logging.INFO)


async def consume_messages():
    config = get_config()  # It's better to access config inside async functions if it's needed dynamically
    consumer = AIOKafkaConsumer(
        config.KAFKA_TOPIC,
        bootstrap_servers=config.KAFKA_SERVER,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group-id',
        value_deserializer=lambda x: loads(x.decode('utf-8'))
    )
    await consumer.start()
    logging.info("Kafka Consumer has started.")
    chat_model = setup_chat_model()

    try:
        async for message in consumer:
            logging.debug(f"Received message: {message}")
            processed_docs = process_message(message, chat_model)
            await produce_messages(processed_docs)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
    finally:
        await consumer.stop()
        logging.info("Kafka Consumer has closed.")


async def produce_messages(processed_documents):
    config = get_config()

    producer = AIOKafkaProducer(
        bootstrap_servers=config.KAFKA_SERVER,
        value_serializer=custom_serializer
    )

    # Start both consumer and producer
    await producer.start()
    logging.info("Kafka Producer have started.")

    try:

        logging.debug(f"Received message to send to vector db:{processed_documents[0].metadata}")
        await producer.send(config.VECTORDB_TOPIC_NAME, processed_documents)

    except Exception as e:
        logging.error(f"Error in consuming or producing message: {e}")

    finally:

        await producer.stop()
        logging.info("Kafka  Producer have closed.")


@app.on_event("startup")
async def startup_event():
    config = get_config()
    if await check_kafka_connection(config.KAFKA_SERVER, config.KAFKA_TOPIC):  # Make sure this function is async
        logging.info("Starting up the consumer background task.")
        asyncio.create_task(consume_messages())
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
