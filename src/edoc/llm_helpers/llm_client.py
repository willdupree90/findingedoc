import os
from abc import ABC, abstractmethod

# Direct OpenAI SDK
from openai import OpenAI
from openai import AzureOpenAI

# LangChain SDK
from langchain_openai import ChatOpenAI, AzureChatOpenAI


class BaseLLM(ABC):
    """
    Abstract base class for LLM clients. All clients must implement chat_completion.
    """
    @abstractmethod
    def chat_completion(self, messages: list[dict], **kwargs) -> str:
        """
        Send a chat completion request to the underlying LLM service.
        Args:
            messages (list[dict]): List of OpenAI-style message dicts.
            **kwargs: Provider-specific parameters.
        Returns:
            str: The LLM response content.
        """
        pass


class OpenAIClient(BaseLLM):
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)

    def chat_completion(self, messages: list[dict], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


class LangChainClient(BaseLLM):
    def __init__(self, api_key: str = None, model_name: str = None, **kwargs):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=self.api_key,
            temperature=1.0,
            **kwargs
        )

    def chat_completion(self, messages: list[dict], **kwargs) -> str:
        response = self.llm(messages=messages, **kwargs)
        return response.content


class LangChainAzureClient(BaseLLM):
    def __init__(
        self,
        deployment_name: str = None,
        endpoint: str = None,
        api_key: str = None,
        api_version: str = None,
        model_name: str = None,
        **kwargs
    ):
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.llm = AzureChatOpenAI(
            azure_deployment=self.deployment_name,
            openai_api_key=self.api_key,
            openai_api_version=self.api_version,
            model=self.model_name,
            temperature=1.0,
            **kwargs
        )

    def chat_completion(self, messages: list[dict], **kwargs) -> str:
        response = self.llm(messages=messages, **kwargs)
        return response.content


class AzureClient(BaseLLM):
    def __init__(
        self,
        deployment_name: str = None,
        endpoint: str = None,
        api_key: str = None,
        api_version: str = None,
        model_name: str = None
    ):
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def chat_completion(self, messages: list[dict], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


def get_llm_client(
    provider: str = None,
    model_name: str = None,
    **kwargs
) -> BaseLLM:
    """
    Factory function to get an LLM client by provider.

    Args:
        provider (str): "openai", "langchain", "azure", or "langchain-azure".
        model_name (str): Model or deployment name. Defaults to env LLM_MODEL or "gpt-4o-mini".
        **kwargs: Extra args passed to client init.

    Returns:
        BaseLLM: An instance of a client implementing BaseLLM.
    """
    model = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")

    if provider == "openai":
        return OpenAIClient(api_key=kwargs.get("api_key"), model_name=model)
    elif provider == "langchain":
        return LangChainClient(api_key=kwargs.get("api_key"), model_name=model, **kwargs)
    elif provider in ("langchain-azure", "azure-langchain"):
        return LangChainAzureClient(
            deployment_name=model,
            api_key=kwargs.get("api_key"),
            api_base=kwargs.get("endpoint"),
            api_version=kwargs.get("api_version"),
            **kwargs
        )
    elif provider == "azure":
        return AzureClient(
            endpoint=kwargs.get("endpoint"),
            api_key=kwargs.get("api_key"),
            api_version=kwargs.get("api_version"),
            model_name=model
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
