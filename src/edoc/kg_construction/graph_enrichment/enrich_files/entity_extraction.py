import os

from pydantic import BaseModel, Field
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate

from edoc.llm_helpers.llm_client import get_llm_client

class Parameter(BaseModel):
    """Model representing a function or class parameter."""
    name: str
    type: str

class FunctionEntity(BaseModel):
    """Model representing a function entity."""
    name: str
    parameters: List[Parameter]
    return_type: Optional[str] = None

class ClassEntity(BaseModel):
    """Model representing a class entity."""
    name: str
    parameters: List[Parameter]

class ImportEntity(BaseModel):
    """Model representing an import entity."""
    module: str
    entities: List[str]

class CodeEntities(BaseModel):
    """Identifying information about code entities."""
    
    imports: List[ImportEntity] = Field(
        default=[],
        description="All the import statements in the code, with the module "
        "and specific entities being imported.",
    )
    functions: List[FunctionEntity] = Field(
        default=[],
        description="All the function names in the code, including their parameters, returns, "
        "and types if available.",
    )
    classes: List[ClassEntity] = Field(
        default=[],
        description="All the class names in the code, including their parameters "
        "and types if available.",
    )

def extract_code_entities(code_string, model='gpt-4o-mini'):
    """
    Extracts code entities from a given code string, including imports, function names, and class names.

    This function uses a language model to analyze the provided code string and extract relevant code entities. 
    For imports, it identifies the module and specific entities being imported. For functions and classes, it 
    captures their names, parameters, and types if available.

    Args:
        code_string (str): The code snippet as a string from which to extract entities.
        model (str): The LLM model to use
        
    Returns:
        entities: An instance of CodeEntities containing the extracted imports, functions, and classes.
    """

    llm_client = get_llm_client(
        provider=os.getenv("LANGCHAIN_PROVIDER", "langchain"),
        model_name=model
    )
    llm = llm_client.llm

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are extracting imports, function names, and class names from the given code. "
                "For imports, provide the module and specific entities being imported. "
                "For functions and classes, include their parameters and types if available.",
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {code_snippet}",
            ),
        ]
    )

    entity_chain = prompt | llm.with_structured_output(CodeEntities)

    entities = entity_chain.invoke({'code_snippet': code_string})

    entities = entities.dict()

    return entities