import os
from edoc.gpt_helpers.gpt_basics import create_chat_completion
from pydantic import BaseModel, Field
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import Language

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
        {"role": "user", "content": f"""You are helping to summarize code chunks. 
        Please summarize the given chunk of text from the file `{file_name}`. 
        Keep the summary brief and clear, focusing on what the code does.

        The chunk codes is: {chunk_text}

        Please format summaries in markdown using this tempalte:
        **Summary**:
        <fill in>"""}
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
        print(f"An error occurred while reading the file [{file_path}]: {e}")
        return None

def should_skip_file(file_path, custom_skip_extensions=None, limit_size=True, size_limit_mb=5):
    """
    Determine if a file should be skipped based on its type or size.

    Args:
        file_path (str): The path to the file.
        custom_skip_extensions (list[str], optional): Custom list of file extensions to skip.
        limit_size (bool): Whether to skip files larger than the size limit. Default is True.
        size_limit_mb (int): The size limit in megabytes for files to skip. Default is 5MB.

    Returns:
        bool: True if the file should be skipped, False otherwise.
    """
    # Get the file extension
    _, ext = os.path.splitext(file_path)

    default_skip_extensions = {
        '.lock', '.png', '.jpg', '.gif', '.pdf', '.zip', '.class', '.o', '.out',
        '.md', '.rst', '.csv', '.tsv'
    }

    if custom_skip_extensions:
        skip_extensions = default_skip_extensions.union(set(custom_skip_extensions))
    else:
        skip_extensions = default_skip_extensions

    skip_directories = {'node_modules', '.git', '.svn'}

    if ext.lower() in skip_extensions:
        return True

    if any(skip_dir in file_path for skip_dir in skip_directories):
        return True

    if limit_size and os.path.getsize(file_path) > size_limit_mb * 1024 * 1024:
        return True

    return False

def get_text_splitter(file_path, chunk_size, chunk_overlap):
    """
    Determine the appropriate RecursiveCharacterTextSplitter based on the file extension.

    Args:
        file_path (str): The path to the file.
        chunk_size (int): The size of the chunks. Default is 50.
        chunk_overlap (int): The number of overlapping characters between chunks. Default is 0.

    Returns:
        tuple: A tuple containing the RecursiveCharacterTextSplitter and a string indicating the language used.
    """

    extension_to_language = {
        ".cpp": Language.CPP,
        ".go": Language.GO,
        ".java": Language.JAVA,
        ".kt": Language.KOTLIN,
        ".js": Language.JS,
        ".ts": Language.TS,
        ".tsx": Language.TS, #Not in their docs but tsx is ts?
        ".php": Language.PHP,
        ".proto": Language.PROTO,
        ".py": Language.PYTHON,
        ".rst": Language.RST,
        ".rb": Language.RUBY,
        ".ex": Language.ELIXIR,
        ".exs": Language.ELIXIR,
        ".rs": Language.RUST,
        ".scala": Language.SCALA,
        ".swift": Language.SWIFT,
        ".md": Language.MARKDOWN,
        ".tex": Language.LATEX,
        ".html": Language.HTML,
        ".sol": Language.SOL,
        ".cs": Language.CSHARP,
        ".cbl": Language.COBOL,
        ".lua": Language.LUA,
        ".hs": Language.HASKELL,
        
    }

    _, extension = os.path.splitext(file_path)

    language = extension_to_language.get(extension.lower(), Language.PYTHON)

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    return splitter, f"{language.name}"
