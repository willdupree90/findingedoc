import os
import sys
from dotenv import load_dotenv
import argparse
from pathlib import Path
from edoc.gpt_helpers.connect import connect_to_neo4j
from edoc.gpt_helpers.connect import OpenAiConfig

from edoc.kg_construction.processing_tools.file_system_processor import FileSystemProcessor
from edoc.kg_construction.build_tools.graph_builder import GraphBuilder
from edoc.kg_construction.summary_tools.summary_manager import SummaryManager

from tqdm import tqdm
import time

def hacky_progress_step(title, n = 10, time_on_screen=3):
    for i in tqdm(range(n), desc=title):
        time.sleep(time_on_screen/n)

    return

class CodebaseGraph:
    def __init__(
            self, 
            root_directory, 
            uri="bolt://localhost:7687", 
            user=None, 
            password=None, 
            openai_api_key=None,
            chunk_size=3500,
            chunk_overlap=50
    ):
        """
        Initialize the CodebaseGraph with a connection to Neo4j.

        Args:
            root_directory (str): The directory to be extracted into knowledge.
            uri (str): The URI of the Neo4j database. Defaults to localhost.
            user (str): Username for Neo4j. If None, loads from environment variable NEO4J_USERNAME.
            password (str): Password for Neo4j. If None, loads from environment variable NEO4J_PASSWORD.
            openai_api_key (str): Key needed to access OpenAI API
            chunk_size (int): size of chunk to use (by number of tokens)
            chunk_overlap (int): number of chunks to overlap when splitting
        """
        load_dotenv()

        self.uri = uri
        self.NEO4J_USER = user or os.getenv("NEO4J_USERNAME")
        self.NEO4J_PASSWORD =  password or os.getenv("NEO4J_PASSWORD")
        self.OPENAI_API_KEY = openai_api_key or OpenAiConfig.get_openai_api_key()

        if not self.NEO4J_USER or not self.NEO4J_PASSWORD:
            raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD must be provided either as arguments or environment variables.")
        
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be provided, set as param or check env file.")

        self.kg = connect_to_neo4j()

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.fs_processor = FileSystemProcessor(root_directory)
        self.graph_builder = GraphBuilder(
            self.kg, 
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        self.summary_manager = SummaryManager(self.kg)

    def create_graph(self):
        hacky_progress_step(title="Initiating graph...", time_on_screen=1)
        hacky_progress_step(title="Walking directory and created Directory and File nodes...")
        self.fs_processor.load_dirs_and_files_to_graph(self.kg)
        self.graph_builder.enrich_graph()
        self.summary_manager.automate_summarization()
        self.graph_builder.create_all_vector_indexes()

def main(path=None):
    """
    Main function to initiate the graph creation process.
    It checks for a provide path or a CLI input path to a directory that holds code.
    """

    load_dotenv()

    seed_data = path

    if not seed_data:
        parser = argparse.ArgumentParser(description='Seed the knowledge graph with data from a specified directory.')
        parser.add_argument('path', type=str, nargs='?', help='The path to the directory to be processed.')
        args = parser.parse_args()
        seed_data = args.path

    if not seed_data:
        print("Error: No seed data directory provided. Provide a path as a CLI argument.")
        sys.exit(1)  # Exit with a non-zero status to indicate an error

    # Convert the path to a Path object for robust handling
    seed_data = Path(seed_data).resolve()

    if not seed_data.is_dir():
        print(f"Error: The provided path '{seed_data}' is not a valid directory.")
        sys.exit(1)

    try:
        graph = CodebaseGraph(root_directory=seed_data)
        graph.create_graph()
        print(f"Graph successfully created from directory: {seed_data}")
    except Exception as e:
        print(f"An error occurred while creating the graph: {e}")
        sys.exit(1)  # Exit with a non-zero status if an error occurs

if __name__ == "__main__":
    main()



        
