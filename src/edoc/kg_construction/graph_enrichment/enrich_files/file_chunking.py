import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import Language

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

def should_skip_file_or_dir(file_path, custom_skip_extensions=None, limit_size=True, size_limit_mb=5):
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
        '.md', '.rst', '.csv', '.tsv', '.pyc'
    }

    if custom_skip_extensions:
        skip_extensions = default_skip_extensions.union(set(custom_skip_extensions))
    else:
        skip_extensions = default_skip_extensions

    skip_keywords = {'node_modules', '.git', '.svn', '__pycache__', 'egg-info', '.env'}

    if ext.lower() in skip_extensions:
        return True

    if any(keyword in file_path for keyword in skip_keywords):
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
