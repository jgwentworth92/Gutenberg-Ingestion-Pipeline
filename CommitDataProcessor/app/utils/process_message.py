from json import dumps

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
    return rtn_documents


def create_documents(event_data):
    documents = []
    for file in event_data['files']:
        doc = create_document(file, event_data)
        documents.append(doc)
    return documents


def create_document(file, event_data):
    page_content = f"Filename: {file['filename']}, Status: {file['status']} files: {file['patch']}"
    metadata = {
        "filename": file['filename'],
        "status": file['status'],
        "additions": file['additions'],
        "deletions": file['deletions'],
        "changes": file['changes'],
        "author": event_data['author'],
        "date": event_data['date'],
        "commit_url": event_data['url'],
        "id": event_data['commit_id'],
        "token_count": len(page_content.split())
    }
    return Document(page_content=page_content, metadata=metadata)
