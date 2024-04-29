import json
from typing import List

from fastapi import APIRouter, HTTPException, Request, Body
import logging
from github import Github, GithubException

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


@router.post("/add-webhook")
async def add_webhook(
        token: str = Body(..., embed=True),
        username: str = Body(..., embed=True),
        repository: str = Body(..., embed=True)
):
    g = Github(token)
    try:
        repo = g.get_repo(f"{username}/{repository}")
        # Specify the events you want to trigger the webhook
        events = ["push", "pull_request"]
        githutb_config = {
            "url": config.CALLBACK_URL,
            "content_type": "json"
        }
        # Create the webhook
        webhook = repo.create_hook(name="web", config=githutb_config, events=events, active=True)
        return {"status": "Webhook created", "id": webhook.id}
    except GithubException as e:
        logging.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=400, detail=f"GitHub API error: {e.data.get('message', 'Unknown error')}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def fetch_and_process_commits(owner, repo_name, token, commit_id=None):
    g = Github(token)
    repo = g.get_repo(f"{owner}/{repo_name}")
    commits = [repo.get_commit(commit_id)] if commit_id else repo.get_commits()

    commit_models = []
    for commit in commits:
        commit_models.append(CommitData(
            author=commit.commit.author.name,
            message=commit.commit.message,
            date=commit.commit.author.date.isoformat(),
            url=commit.html_url,
            commit_id=commit.sha,
            files=[FileInfo(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=getattr(file, 'patch', None)
            ) for file in commit.files]
        ))

    return await process_commits(commit_models, config.KAFKA_TOPIC)


# Endpoint for webhook handling
@router.post("/webhook")
async def handle_webhook(request: Request):
    event_data = await request.json()
    logging.info("Received webhook data: %s", event_data)

    if 'commits' in event_data and 'repository' in event_data:
        owner = event_data['repository']['owner']['login']
        repo = event_data['repository']['name']
        commit_id = event_data['commits'][0]['id']  # Process the first commit for simplicity
        results = await fetch_and_process_commits(owner, repo, config.GITHUB_ACCESS_TOKEN, commit_id)
        return {"status": "Processed", "results": results}

    return {"status": "Received", "data": "No relevant data to process"}


# Endpoint to handle repository set
@router.post("/repository/{owner}/{repo_name}")
async def set_repository(owner: str, repo_name: str):
    if not repo_name or not owner:
        raise HTTPException(status_code=400, detail="Repository name and owner are required.")

    results = await fetch_and_process_commits(owner, repo_name, config.GITHUB_ACCESS_TOKEN)
    return {"status": "Processed", "results": results}


# Function to process commits to Kafka
async def process_commits(commits, kafka_topic):
    producer = AIOKafkaProducer(
        bootstrap_servers=config.KAFKA_SERVER,
        value_serializer=lambda x: dumps(x).encode('utf-8')
    )
    await producer.start()
    results = []
    try:
        for commit in commits:
            await producer.send_and_wait(kafka_topic, commit.dict())
            results.append(f"Sent commit {commit.commit_id} by {commit.author}")
            logging.info(f"Sent commit by {commit.author} at {commit.date}")
    except Exception as e:
        logging.error(f"Error in sending commits to Kafka: {e}")
    finally:
        await producer.stop()
    return results
