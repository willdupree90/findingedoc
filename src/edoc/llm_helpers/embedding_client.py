import os
from abc import ABC, abstractmethod

# Direct OpenAI SDK
from openai import OpenAI
from openai import AzureOpenAI

# LangChain Embeddings SDK
from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings


class BaseEmbedding(ABC):
    """
    Abstract base class for embedding clients. All clients must implement embed().
    """
    @abstractmethod
    def embed(self, text: str, **kwargs) -> list[float]:
        """
        Generate an embedding vector for the given text.
        Args:
            text (str): The input text to embed.
            **kwargs: provider-specific parameters.
        Returns:
            list[float]: The embedding vector.
        """
        pass


class OpenAIEmbeddingClient(BaseEmbedding):
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = OpenAI(api_key=self.api_key)

    def embed(self, text: str, **kwargs) -> list[float]:
        sanitized = text.replace("\n", " ")
        response = self.client.embeddings.create(
            input=[sanitized],
            model=self.model_name,
            **kwargs
        )
        return response.data[0].embedding


class LangChainEmbeddingClient(BaseEmbedding):
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embeddings = OpenAIEmbeddings(
            model=self.model_name,
            openai_api_key=self.api_key
        )

    def embed(self, text: str, **kwargs) -> list[float]:
        return self.embeddings.embed_query(text)


class LangChainAzureEmbeddingClient(BaseEmbedding):
    def __init__(
        self,
        model_name: str = None,
        azure_endpoint: str = None,
        api_key: str = None,
        openai_api_version: str = None,
    ):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_api_version = openai_api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        # Use LangChain's AzureOpenAIEmbeddings class
        self.embeddings = AzureOpenAIEmbeddings(
            model=self.model_name,
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            openai_api_version=self.openai_api_version
        )

    def embed(self, text: str, **kwargs) -> list[float]:
        return self.embeddings.embed_query(text)


class AzureEmbeddingClient(BaseEmbedding):
    def __init__(
        self,
        endpoint: str = None,
        api_key: str = None,
        api_version: str = None,
        model_name: str = None
    ):
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def embed(self, text: str, **kwargs) -> list[float]:
        sanitized = text.replace("\n", " ")
        response = self.client.embeddings.create(
            input=[sanitized],
            model=self.model_name,
            **kwargs
        )
        return response.data[0].embedding


def get_embedding_client(
    provider: str = None,
    model_name: str = None,
    **kwargs
) -> BaseEmbedding:
    """
    Factory function to get an embedding client by provider.

    Args:
        provider (str): "openai", "langchain", "azure", or "langchain-azure".
        model_name (str): Model name or deployment. Defaults to env EMBEDDING_MODEL or "text-embedding-3-small".
        **kwargs: Extra args passed to client init.

    Returns:
        BaseEmbedding: An instance of a client implementing BaseEmbedding.
    """
    model = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    if provider == "openai":
        return OpenAIEmbeddingClient(api_key=kwargs.get("api_key"), model_name=model)
    elif provider == "langchain":
        return LangChainEmbeddingClient(api_key=kwargs.get("api_key"), model_name=model)
    elif provider in ("langchain-azure", "azure-langchain"):
        return LangChainAzureEmbeddingClient(
            model_name=model,
            azure_endpoint=kwargs.get("azure_endpoint"),
            api_key=kwargs.get("api_key"),
            openai_api_version=kwargs.get("openai_api_version")
        )
    elif provider == "azure":
        return AzureEmbeddingClient(
            endpoint=kwargs.get("endpoint"),
            api_key=kwargs.get("api_key"),
            api_version=kwargs.get("api_version"),
            model_name=model
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
