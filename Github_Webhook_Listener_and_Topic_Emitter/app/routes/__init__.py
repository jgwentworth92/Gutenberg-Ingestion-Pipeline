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
import httpx
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
config = get_config()

router = APIRouter(
    prefix="/github",
    tags=["GitHub Operations"],
    responses={404: {"description": "Not found"}}
)


async def get_commit_details(commit_id: str, repo: str, owner: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_id}"
    headers = {"Authorization": f"token {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json()

@router.post("/webhook")
async def handle_webhook(request: Request):
    try:
        event_data = await request.json()
        ic("Received webhook data:", event_data)

        if 'commits' in event_data and 'repository' in event_data:
            owner = event_data['repository']['owner']['login']
            repo = event_data['repository']['name']
            commit_details = []

            for commit in event_data['commits']:
                # Fetch detailed commit data including files
                detailed_commit = await get_commit_details(commit['id'], repo, owner, config.GITHUB_ACCESS_TOKEN)
                commit_data = CommitData(
                    author=detailed_commit['commit']['author']['name'],
                    message=detailed_commit['commit']['message'],
                    date=detailed_commit['commit']['author']['date'],
                    url=detailed_commit['html_url'],
                    commit_id=commit['id'],
                    files=[FileInfo(**file) for file in detailed_commit.get('files', [])]
                )
                commit_details.append(commit_data)

            results = await process_commits(commit_details, "your-kafka-topic")
            return {"status": "Processed", "results": results}

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
