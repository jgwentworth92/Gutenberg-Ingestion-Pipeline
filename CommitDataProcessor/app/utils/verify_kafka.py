import asyncio
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from json import loads

from app.config import get_config


async def check_kafka_connection(bootstrap_servers, topic, timeout=60):
    config = get_config()
    end_time = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end_time:
        try:
            # Create asynchronous producer and consumer
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='my-group-id',
                value_deserializer=lambda x: loads(x.decode('utf-8'))
            )

            # Start producer and consumer
            await producer.start()
            await consumer.start()
            topics = await consumer.topics()

            if topic in topics:
                logging.info(f"Kafka is ready and the topic is available: {topics}")
                await producer.stop()
                await consumer.stop()
                return True

            logging.info("Kafka is up but topic is not available yet.")
            await producer.stop()
            await consumer.stop()
        except Exception as e:
            logging.warning(f"Waiting for Kafka to be ready: {e}")
        await asyncio.sleep(5)  # wait for 5 seconds before trying again

    logging.error("Kafka connection could not be established within the timeout period.")
    return False
