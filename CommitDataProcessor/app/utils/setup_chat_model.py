from typing import List
from icecream import ic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.fake import FakeMessagesListChatModel
from langchain_core.messages import BaseMessage

from app.config import get_config

config=get_config()

from fastapi import Depends


def get_openai_chat_model():
    chat_model = ChatOpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model="gpt-3.5-turbo")
    return chat_model


def get_fake_chat_model():
    fake_responses: List[BaseMessage] = [BaseMessage(content="This is a fake response.", type="text")]
    chat_model = FakeMessagesListChatModel(responses=fake_responses)
    return chat_model


# Additional model setups can be defined similarly

def setup_chat_model():
    # Based on the model type specified in the configuration, use the corresponding setup function
    if config.MODEL_PROVIDER == 'openai':
        ic("open ai model is being used")
        model_setup_function = get_openai_chat_model
    elif config.MODEL_PROVIDER == 'fake':
        ic("Fake model is being used")
        model_setup_function = get_fake_chat_model
    else:
        raise ValueError(f"Unsupported chat model provider: {config.MODEL_PROVIDER}")

    # Call the selected setup function to get the chat model
    chat_model = model_setup_function()
    prompt = ChatPromptTemplate.from_template(config.TEMPLATE)
    return prompt | chat_model | StrOutputParser()
