from gptBasics import create_chat_completion
from pydantic import BaseModel, Field
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def summarize_file_chunk(chunk_text, file_name, model='gpt-4o-mini'):
    """
    Summarize a chunk of text from a file using OpenAI's language model.

    Args:
        chunk_text (str): The text chunk to summarize.
        file_name (str): The name of the file from which the chunk was extracted.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.

    Returns:
        str: A brief and clear summary of the chunk.
    """
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"I have this text from a file named {file_name}. The text is:\n{chunk_text}\nPlease summarize it in simple terms. Try to keep the summary brief, but maintain clarity."}
    ]
    return create_chat_completion(messages=prompt, model=model)

def summarize_list_of_summaries(summaries, model='gpt-4o-mini'):
    """
    Summarize a chunk of text from a file using OpenAI's language model.

    Args:
        summaries (lst[str]): The text chunk to summarize.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.

    Returns:
        str: A brief and clear summary of the chunk.
    """
    context = '\n'.join(summaries)

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"I have these summaries {context}. \nPlease merge them into ovearching themes by summarizing them in simple terms. Try to keep the summary brief, but maintain clarity."}
    ]
    return create_chat_completion(messages=prompt, model=model)

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

    llm=ChatOpenAI(
        model_name=model
    )
    # Modify the prompt to focus on extracting code entities
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

    # Set up the chain to extract the structured output
    entity_chain = prompt | llm.with_structured_output(CodeEntities)

    entities = entity_chain.invoke({'code_snippet': code_string})

    entities = entities.dict()

    return entities

def read_file_contents(file_path):
    """
    Opens a file and reads its contents as text.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = file.read()
        return contents
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None