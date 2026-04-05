from typing import Annotated

from langchain.messages import AnyMessage
from langchain_ollama import ChatOllama
from langgraph.graph import add_messages
from pydantic import BaseModel, ConfigDict

from bases import base_alchemy_pg_client, base_qdrant_client


class RuntimeContext(BaseModel):
    """
    Runtime context
    """

    qdrant_client: base_qdrant_client.BaseQdrantClient
    pg_client: base_alchemy_pg_client.BaseAlchemyPGClient
    ollama_client: ChatOllama

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GraphState(BaseModel):
    """
    Graph overall state
    """

    messages: Annotated[list[AnyMessage], add_messages]
