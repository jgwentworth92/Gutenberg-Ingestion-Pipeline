import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Example to add more specific handlers or filters
    logger = logging.getLogger('kafka')
    logger.setLevel(logging.DEBUG)  # Set this to DEBUG to get detailed logs from the Kafka consumer
