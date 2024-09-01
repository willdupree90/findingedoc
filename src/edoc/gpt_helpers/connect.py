from langchain_community.graphs import Neo4jGraph
import os
from dotenv import load_dotenv

def connect_to_neo4j(uri: str = "bolt://localhost:7687") -> Neo4jGraph:
    """
    Connect to a Neo4j graph database.

    This function connects to a Neo4j graph database using the provided URI.
    By default, it connects to the local Neo4j instance at "bolt://localhost:7687".
    The function loads the username and password from environment variables using the dotenv package.

    Args:
        uri (str): The URI of the Neo4j database to connect to. Defaults to "bolt://localhost:7687".

    Returns:
        Neo4jGraph: An instance of the Neo4jGraph connected to the specified database.

    Raises:
        ValueError: If the username or password environment variables are not set.
    """
    # Load environment variables from a .env file
    load_dotenv()

    # Retrieve username and password from environment variables
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not username or not password:
        raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD environment variables must be set.")

    # Create and return the Neo4jGraph instance
    graph = Neo4jGraph(url=uri, username=username, password=password)
    return graph
