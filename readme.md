
# Gutenberg Ingestion Pipeline

This project integrates a series of microservices designed to process and store GitHub event data into a vector database. The architecture comprises three main microservices, each responsible for a distinct part of the data processing and storage pipeline. Below is an overview of each microservice and its role within the system.

## 1.GitHub Webhook Listener and Topic Emitter

### Purpose:
This microservice is the initial stage of the Gutenberg Ingestion Pipeline. It acts as the gateway for GitHub events, capturing webhook notifications for repository activities like commits and pull requests.

### Key Features:
- **Event Listening:** Monitors GitHub webhook events, providing real-time responsiveness to repository changes.
- **Data Extraction:** Extracts important data from webhook payloads, focusing on commit information relevant to the pipeline.
- **Message Publishing:** Publishes formatted data onto a Kafka topic, facilitating the flow to subsequent services.


### Integration:
- **Connects with:** Data processed by this service is consumed by the "Commit Data Processor". This ensures a smooth flow of data through the pipeline.

### Endpoints:
- **POST `/github/add-webhook`**: Adds a webhook to a specified GitHub repository. This setup allows the repository to send notifications to the `CALLBACK_URL`.
- **POST `/github/webhook`**: Handles incoming webhook notifications, processing data to emit to Kafka.
- **POST `/github/repository/{owner}/{repo_name}`**: Processes all commits from a specified repository at once, sending them directly to Kafka.

## 2. Commit Data Processor

### Purpose:
The "Commit Data Processor" serves as the middle layer in the Gutenberg Ingestion Pipeline, facilitating the transfer and transformation of commit data from the "GitHub Webhook Listener and Topic Emitter" to the "Vector DB Ingestor".

### Key Features:
- **Message Consumption:** Consumes messages from a Kafka topic filled with data from the upstream microservice.
- **Data Processing and Enrichment:** Processes each file in a commit using NLP to summarize and enhance the data.
- **Message Production:** Outputs the processed data to another Kafka topic for consumption by the next microservice in the pipeline.

### Integration:
- **Receives from:** Consumes from a Kafka topic that receives commit data.
- **Sends to:** Emits processed and enriched data to another Kafka topic targeted at the "Vector DB Ingestor".

### Processing Workflow:
1. **Receive Data:** Data arrives through Kafka from the "GitHub Webhook Listener and Topic Emitter".
2. **Summarize and Enrich:** Summarizes the contents of each file in the commit using an LLM, adding enhanced summaries to the metadata.
3. **Emit Processed Data:** Forwards the enriched documents to a Kafka topic designated for the vector database ingestion.

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
-  `CALLBACK_URL`: url used for callback on webhooks by ngrok.

#### GitHub Webhook Listener and Topic Emitter
- `GITHUB_ACCESS_TOKEN`: Your GitHub access token for authenticating GitHub API requests
- `REPO_NAME`: The name of the GitHub repository to listen to
- `CALLBACK_URL`: Endpoint URL configured in GitHub for receiving webhook notifications.

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
