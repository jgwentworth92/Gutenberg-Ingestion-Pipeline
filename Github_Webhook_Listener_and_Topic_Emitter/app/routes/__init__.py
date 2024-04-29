from fastapi import FastAPI, APIRouter, Request, HTTPException
from kafka import KafkaProducer
from json import dumps
from github import Github
from icecream import ic
import logging
import os

from app.config import get_config

# Create an APIRouter instance
router = APIRouter(
    prefix="/github",  # This is the base path for all endpoints defined in this router.
    tags=["GitHub Operations"],  # Tags used for grouping endpoints in the docs
    responses={404: {"description": "Not found"}}
)

config = get_config()

GITHUB_ACCESS_TOKEN = config.GITHUB_ACCESS_TOKEN
REPO_NAME = config.REPO_NAME
KAFKA_SERVER = config.KAFKA_SERVER
KAFKA_TOPIC = config.KAFKA_TOPIC

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


@router.post("/webhook")
async def handle_webhook(request: Request):
    event_data = await request.json()
    for event in event_data:
        ic(event)
    return {"status": "Processed"}


@router.post("/set_repo")
async def set_repository(repo_name: str):
    if not repo_name:
        raise HTTPException(status_code=400, detail="Repository name is required.")

    results = process_commits(GITHUB_ACCESS_TOKEN, repo_name)
    return {"status": results}


def process_commits(access_token, repo_name):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda x: dumps(x).encode('utf-8'),
        retries=5,
        retry_backoff_ms=300,
        acks='all',
        request_timeout_ms=5000
    )

    g = Github(access_token)
    repo = g.get_repo(repo_name)
    commits = repo.get_commits()
    results = []

    for commit in commits:
        files_info = []
        for file in commit.files:
            file_data = {
                'filename': file.filename,
                'status': file.status,
                'additions': file.additions,
                'deletions': file.deletions,
                'changes': file.changes,
                'patch': file.patch if file.patch else None
            }
            files_info.append(file_data)
            ic(file_data['changes'])

        data = {
            'author': commit.author.login if commit.author else "Unknown",
            'message': commit.commit.message,
            'date': str(commit.commit.author.date),
            'url': commit.html_url,
            'commit_id': commit.sha,
            'files': files_info
        }

        producer.send(KAFKA_TOPIC, value=data)
        logging.info(f"Sent commit by {data['author']} at {data['date']} with files changes.")
        results.append(
            f"Sent commit {data['commit_id']} by {data['author']} at {data['date']} with commit message {data['message']}.")

    return results
