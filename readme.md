
# Gutenberg Ingestion Pipeline

This project integrates a series of microservices designed to process and store GitHub event data into a vector database. The architecture comprises three main microservices, each responsible for a distinct part of the data processing and storage pipeline. Below is an overview of each microservice and its role within the system.

## 1. GitHub Webhook Listener and Topic Emitter

### Purpose:
This microservice acts as an entry point for GitHub webhook events. It listens for notifications of new commits or changes to repositories.

### Key Features:
- **Event Listening:** Captures real-time events from GitHub via webhooks.
- **Data Extraction:** Parses and processes data from each event.
- **Message Publishing:** Emits processed data to a designated Kafka topic for downstream processing.

## 2. Commit Data Processor

### Purpose:
This microservice consumes messages from the Kafka topic populated by the GitHub Webhook Listener and processes them to prepare for vector database ingestion.

### Key Features:
- **Data Transformation:** Performs necessary transformations and enrichments on the commit data.
- **Enhanced Processing:** Applies additional logic to refine the data based on predefined rules or models.
- **Forwarding Data:** Sends the processed data to another Kafka topic, specifically tailored for the vector DB ingestion service.

## 3. Vector DB Ingestor

### Purpose:
Responsible for ingesting processed data into Qdrant, a vector database, which facilitates advanced data retrieval techniques.

### Key Features:
- **Data Ingestion:** Subscribes to the Kafka topic to receive processed data.
- **Vectorization:** Utilizes embedding models to convert textual data into vector representations.
- **Database Storage:** Stores the vectorized data in Qdrant, ensuring it is optimized for quick retrieval and efficient searches.

These services are designed to operate in a seamless and loosely coupled manner, promoting scalability and robustness across the data processing pipeline.

## Getting Started

This section provides instructions on how to set up and run the microservices using Docker Compose. Each microservice is containerized, making it straightforward to manage dependencies and configurations.

### Prerequisites

Before you begin, ensure you have the following installed on your system:
- Docker
- Docker Compose

You will also need to set up environment variables required by each service. These variables can be defined in a `.env` file in the root directory of your project.

### Environment Variables

Below are the environment variables required by each microservice:

#### General
- `KAFKA_BOOTSTRAP_SERVERS`: Address of the Kafka server (e.g., `localhost:9092`)
- `VECTORDB_TOPIC_NAME`: The Kafka topic name for vector database operations

#### GitHub Webhook Listener and Topic Emitter
- `GITHUB_ACCESS_TOKEN`: Your GitHub access token for authenticating GitHub API requests
- `REPO_NAME`: The name of the GitHub repository to listen to

#### Commit Data Processor
- `MODEL_PROVIDER`: Provider of the model, if using different ML models
- `OPENAI_API_KEY`: API key for OpenAI, if using OpenAI models
- `TEMPLATE`: Template string for to be used for summary prompt

#### Vector DB Ingestor
- `VECTOR_DB_HOST`: Hostname for the Qdrant vector database (e.g., `localhost`)
- `VECTOR_DB_PORT`: Port number for the Qdrant vector database (e.g., `6333`)
- `OPENAI_API_KEY`: API key for OpenAI, reused if the same as in Commit Data Processor

### Running the Services

To start all services, navigate to the root directory of your project where the `docker-compose.yml` file is located and run the following command:

```bash
docker-compose up --build
