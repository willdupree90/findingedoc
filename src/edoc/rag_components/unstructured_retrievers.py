import os
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from edoc.gpt_helpers.connect import connect_to_neo4j

load_dotenv()
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
URL = "bolt://localhost:7687"

from edoc.gpt_helpers.connect import OpenAiConfig

OPENAI_API_KEY = OpenAiConfig.get_openai_api_key()

class ProgrammingNamedEntities(BaseModel):
    """Identifying information about code entities."""
    
    entities: List = Field(
        default=[],
        description="Extracted programming specific named entities, such as named directories, "
        "files, functions, classes, or imports in a single list (name matters only).",
    )

def extract_code_entities(string_with_entities, model='gpt-4o-mini'):
    """
    Extracts named entities from a given code string, including directories, files,  imports, function names, and class names.

    This function uses a language model to analyze the provided text and extract named entities related to programming or coding

    Args:
        string_with_entities (str): Unstructured text as a string from which to extract entities.
        model (str): The LLM model to use
        
    Returns:
        entities: An instance of ProgrammingNamedEntities containing the extracted directories, files, imports, functions, and classes.
    """

    llm=ChatOpenAI(
        model_name=model,
        api_key=OPENAI_API_KEY
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are extracting directories, files, imports, functions, and classes from the given text.",
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {code_snippet}",
            ),
        ]
    )

    entity_chain = prompt | llm.with_structured_output(ProgrammingNamedEntities)

    entities = entity_chain.invoke({'code_snippet': string_with_entities})

    entities = entities.entities

    return entities

def create_vector_index(vector_index_name, keyword_index_name, node_label, embedding_property, text_properties, model="text-embedding-3-small", search_type="hybrid"):
    """
    Create a vector index for a given node label and embedding type.
    Quirk is text proprties are returned by string only

    Args:
        vector_index_name (str): The name of the vector index we would like to use.
        keyword_index_name (str) Keyword index name to use (created if run the first time)
        node_label (str): The label of the nodes (e.g., 'Chunk', 'File', 'Directory').
        embedding_property (str): The property name for the embeddings (e.g., 'summary_embedding', 'raw_embedding').
        text_properties (list): List of text properties to include in the index (e.g., ['id', 'summary', 'raw_code']).
        model (str): The OpenAI model to use. Default is 'text-embedding-3-small'.
        search_type (str): The type of search ('hybrid', 'exact', etc.). Default is 'hybrid'.

    Returns:
        Neo4jVector: The vector index object.
    """
    return Neo4jVector.from_existing_graph(
        OpenAIEmbeddings(model=model, api_key=OPENAI_API_KEY),
        url=URL,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        search_type=search_type,
        index_name= vector_index_name,
        keyword_index_name=keyword_index_name,
        node_label=node_label,
        text_node_properties=text_properties,
        embedding_node_property=embedding_property
    )

def perform_similarity_search(vector_indexes, question, top_k=3, additional_metadata=None):
    """
    Perform a similarity search across one or more vector indexes.

    Args:
        vector_indexes (list): A list of Neo4jVector objects to search.
        question (str): The search query.
        top_k (int): The number of top results to return. Default is 3.

    Returns:
        list: A list of top results across all vector indexes.
    """
    results = []
    
    for vector_index in vector_indexes:
        top_n_data = vector_index.similarity_search(question, k=top_k)
        results.extend(top_n_data)

    return [item.page_content for item in results]