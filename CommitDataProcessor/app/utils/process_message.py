from json import dumps

from  app.utils.schema import CommitData, FileInfo
from langchain_core.documents import Document
from icecream import ic


import logging

def serialize_document(doc):
    """Convert a Document instance into a dictionary that can be serialized to JSON."""
    try:
        serialized_doc = {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
        return serialized_doc
    except Exception as e:
        logging.error(f"Failed to serialize document: {e}")
        raise  # Optionally re-raise the exception if you want calling code to handle it as well.

def custom_serializer(documents):
    """Serialize a list of Document objects."""
    try:
        serialized_docs = dumps([serialize_document(doc) for doc in documents]).encode('utf-8')
        return serialized_docs
    except Exception as e:
        logging.error(f"Error serializing documents: {e}")
        raise  # Optionally re-raise the exception if handling further up the call stack is required.

def process_message(message, chain):
    event_data = message.value
    documents = create_documents(event_data)
    rtn_documents = []
    for doc in documents:
        # Invoke the chain to get a summary of the document's page content
        summary = chain.invoke({"text": doc.page_content})

        # Update the document's page content to include the summary
        # This example appends the summary; replace `doc.page_content` with `summary` to overwrite
        updated_doc = Document(page_content=" Summary: " + summary, metadata=doc.metadata)
        rtn_documents.append(doc)
        rtn_documents.append(updated_doc)
        ic(updated_doc.page_content)
        ic("___________________ summary content end___________")
        ic(f"metadata of commit {doc.metadata}")
        ic("___________________ summary content end___________")
        ic(f"page content of commit {doc.page_content}")
    return rtn_documents


def create_documents(event_data):
    documents = []
    for file in event_data['files']:
        doc = create_document(file, event_data)
        documents.append(doc)
    return documents

def create_document(file: FileInfo, event_data: CommitData):
    try:
        # Validate file and event_data with Pydantic
        validated_file = FileInfo(**file)
        validated_event = CommitData(**event_data)

        # Prepare content and metadata
        page_content = f"Filename: {validated_file.filename}, Status: {validated_file.status}, Files: {validated_file.patch}"
        metadata = {
            "filename": validated_file.filename,
            "status": validated_file.status,
            "additions": validated_file.additions,
            "deletions": validated_file.deletions,
            "changes": validated_file.changes,
            "author": validated_event.author,
            "date": validated_event.date,
            "repo_name": validated_event.repo_name,
            "commit_url": validated_event.url,
            "id": validated_event.commit_id,
            "token_count": len(page_content.split())
        }

        # Create Document
        document = Document(page_content=page_content, metadata=metadata)
        return document
    except Exception as e:
        logging.error("Validation error:", e)