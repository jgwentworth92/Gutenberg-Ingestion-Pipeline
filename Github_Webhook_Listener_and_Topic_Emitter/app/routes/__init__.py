import json
from typing import List

from fastapi import APIRouter, HTTPException, Request
import logging
from github import Github
from aiokafka import AIOKafkaProducer
from json import dumps
from schema.github_schema import CommitData, FileInfo  # Import your Pydantic models
from app.config import get_config
from icecream import ic

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
config = get_config()

router = APIRouter(
    prefix="/github",
    tags=["GitHub Operations"],
    responses={404: {"description": "Not found"}}
)


@router.post("/webhook")
async def handle_webhook(request: Request):
    try:
        event_data = await request.json()  # Get the JSON data from the request
        ic("Received webhook data:", event_data)

        if 'commits' in event_data:
            # Convert raw commits to Pydantic models before processing
            commit_models: List[CommitData] = [
                CommitData(
                    author=commit['author']['name'],
                    message=commit['message'],
                    date=commit['timestamp'],
                    url=commit['url'],
                    commit_id=commit['id'],
                    files=[FileInfo(**file) for file in commit['files']]
                ) for commit in event_data['commits']
            ]
            results = await process_commits(commit_models, "your-kafka-topic")
            return {"status": "Processed", "results": results}

        # If no commits are found, just acknowledge the receipt
        return {"status": "Received", "data": "No relevant data to process"}

    except Exception as e:
        logging.error(f"Error in processing webhook: {e}")
        return {"status": "Error", "message": str(e)}


@router.post("/set_repo")
async def set_repository(repo_name: str):
    if not repo_name:
        raise HTTPException(status_code=400, detail="Repository name is required.")
    g = Github(config.GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(repo_name)
    commits = repo.get_commits()
    commit_models = [CommitData(
        author=commit.author.login if commit.author else "Unknown",
        message=commit.commit.message,
        date=str(commit.commit.author.date),
        url=commit.html_url,
        commit_id=commit.sha,
        files=[FileInfo(
            filename=file.filename,
            status=file.status,
            additions=file.additions,
            deletions=file.deletions,
            changes=file.changes,
            patch=file.patch if file.patch else None
        ) for file in commit.files]
    ) for commit in commits]
    results = await process_commits(commit_models, config.KAFKA_TOPIC)
    return {"status": "Processed", "results": results}


async def process_commits(commits, kafka_topic):
    producer = AIOKafkaProducer(
        bootstrap_servers=config.KAFKA_SERVER,
        value_serializer=lambda x: dumps(x).encode('utf-8')
    )
    await producer.start()
    results = []
    try:
        for commit in commits:
            # Now directly using commit.dict() since commits are already validated Pydantic models
            await producer.send_and_wait(kafka_topic, commit.dict())
            results.append(f"Sent commit {commit.commit_id} by {commit.author}")
            logging.info(f"Sent commit by {commit.author} at {commit.date}")
    except Exception as e:
        logging.error(f"Error in processing commits: {e}")
    finally:
        await producer.stop()
    return results
