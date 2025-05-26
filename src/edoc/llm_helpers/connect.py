from langchain_community.graphs import Neo4jGraph
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_neo4j() -> Neo4jGraph:
    """
    Connect to a Neo4j graph database.

    This function connects to a Neo4j graph database using the provided URI.
    By default, it connects to the local Neo4j instance at "bolt://localhost:7687".
    The function loads the username and password from environment variables using the dotenv package.

    Returns:
        Neo4jGraph: An instance of the Neo4jGraph connected to the specified database.

    Raises:
        ValueError: If the username or password environment variables are not set.
    """

    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    uri = os.getenv("NEO4J_URL", "bolt://localhost:7687")

    if not username or not password:
        raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD environment variables must be set.")

    graph = Neo4jGraph(url=uri, username=username, password=password)
    return graph

class OpenAiConfig:
    _api_key = None

    #allows setting of the attribute on the class itself without need to create an instance/object of Config first
    @classmethod
    def get_openai_api_key(cls):
        """
        Returns the current API key. If it is not set dynamically, it will fallback to the environment variable.
        """
        if cls._api_key is not None:
            return cls._api_key
        else:
            # Fallback to the environment variable if the API key is not set dynamically
            return os.getenv("OPENAI_API_KEY")

    @classmethod
    def set_openai_api_key(cls, api_key):
        """
        Dynamically sets the API key. This can overwrite the environment variable.
        """
        cls._api_key = api_key
        # Optionally, overwrite the environment variable in the current session
        os.environ["OPENAI_API_KEY"] = api_key

