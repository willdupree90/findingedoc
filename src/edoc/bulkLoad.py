import os
import json
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from edoc.connect import connect_to_neo4j
from tqdm import tqdm

from langchain.text_splitter import PythonCodeTextSplitter
from gptBasics import create_chat_completion, get_embedding
from fileEnrichment import extract_code_entities, read_file_contents, summarize_file_chunk, summarize_list_of_summaries


import os
import json
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from edoc.connect import connect_to_neo4j
from tqdm import tqdm

from langchain.text_splitter import PythonCodeTextSplitter


import os
import json
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from edoc.connect import connect_to_neo4j
from tqdm import tqdm

from langchain.text_splitter import PythonCodeTextSplitter


class CodebaseGraph:
    def __init__(
            self, 
            root_directory, 
            uri="bolt://localhost:7687", 
            user=None, 
            password=None, 
            openai_api_key=None,
            chunk_size=500,
            chunk_overlap=25
    ):
        """
        Initialize the CodebaseGraph with a connection to Neo4j.

        Args:
            uri (str): The URI of the Neo4j database. Defaults to localhost.
            user (str): Username for Neo4j. If None, loads from environment variable NEO4J_USERNAME.
            password (str): Password for Neo4j. If None, loads from environment variable NEO4J_PASSWORD.
            openai_api_key (str): Key needed to access OpenAI API
        """
        # Load environment variables
        load_dotenv()

        # Set up the Neo4j connection
        self.uri = uri
        self.NEO4J_USER = user or os.getenv("NEO4J_USERNAME")
        self.NEO4J_PASSWORD =  password or os.getenv("NEO4J_PASSWORD")
        self.OPENAI_API_KEY = openai_api_key or os.getenv("OPENAI_API_KEY")

        self.root_directory = root_directory

        if not self.NEO4J_USER or not self.NEO4J_PASSWORD:
            raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD must be provided either as arguments or environment variables.")
        
        if not self.OPENAI_API_KEY:
            raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD must be provided either as arguments or environment variables.")

        self.kg = connect_to_neo4j()

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        

    def get_file_info(self, file_path):
        """
        Get information about a file, including type, size, last modified date, creation date, permissions, owner, and hash.

        Args:
            file_path (str): The path to the file.

        Returns:
            dict: A dictionary containing file information.
        """
        stats = os.stat(file_path)
        file_type = os.path.splitext(file_path)[1][1:]  # Get file extension without the dot
        size = stats.st_size
        last_modified = datetime.fromtimestamp(stats.st_mtime).isoformat()
        created = datetime.fromtimestamp(stats.st_ctime).isoformat()


        return {
            "type": file_type,
            "size": size,
            "last_modified": last_modified,
            "created": created,
        }
    
    def read_file_contents(self, file_path):
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

    def _load_dirs_and_files_to_graph(self):
        """
        Traverse a directory and create a graph in Neo4j representing the directory structure and file information.

        Args:
            root_directory (str): The root directory to start traversing from.
        """
        for root, dirs, files in os.walk(self.root_directory):

            dir_name = os.path.basename(root)

            # Create node for the directory
            self.kg.query(
                """
                MERGE (dir:Directory {name: $dir_name, path: $path})
                ON CREATE SET dir.created = $created, dir.last_modified = $last_modified
                """,
                {
                    'dir_name':dir_name,
                    'path':root,
                    'created':datetime.fromtimestamp(os.stat(root).st_ctime).isoformat(),
                    'last_modified':datetime.fromtimestamp(os.stat(root).st_mtime).isoformat(),
                }
            )

            # Create nodes for subdirectories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                self.kg.query(
                    """
                        MERGE (subdir:Directory {name: $dir_name, path: $subdir_path})
                        ON CREATE SET subdir.created = $created, subdir.last_modified = $last_modified
                        WITH subdir
                        MATCH (parent:Directory {path: $parent_path})
                        MERGE (parent)-[:CONTAINS]->(subdir)
                    """,
                    {
                        'dir_name':dir_name,
                        'subdir_path':dir_path, 
                        'parent_path':root,
                        'created':datetime.fromtimestamp(os.stat(dir_path).st_ctime).isoformat(),
                        'last_modified':datetime.fromtimestamp(os.stat(dir_path).st_mtime).isoformat(),
                    }
                )

            # Create nodes for files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_info = self.get_file_info(file_path)
                self.kg.query(
                    """
                        MERGE (file:File {name: $file_name, path: $file_path})
                        ON CREATE SET file.type = $type, file.size = $size, file.last_modified = $last_modified, file.created = $created
                        WITH file
                        MATCH (parent:Directory {path: $parent_path})
                        MERGE (parent)-[:CONTAINS]->(file)
                    """,
                    {
                        'file_name':file_name, 
                        'file_path':file_path, 
                        'type':file_info['type'], 
                        'size':file_info['size'], 
                        'last_modified':file_info['last_modified'], 
                        'created':file_info['created'], 
                        'parent_path':root
                    }
                )

    def _enrich_graph(self):
        """
        Enriches the knowledge graph by processing files, creating and linking code chunks, and extracting unique code entities.
        """
        text_splitter = PythonCodeTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

        # Query to find files without chunk nodes
        query = """
        MATCH (file:File)
        WHERE NOT (file)-[:CONTAINS]->(:Chunk)
        RETURN file.path AS file_path
        """

        result = self.kg.query(query)
        file_paths = [record['file_path'] for record in result]

        for file in tqdm(file_paths, desc='Creating chunks'):
            file_contents = self.read_file_contents(file)

            if file_contents is not None:
                chunks = text_splitter.split_text(file_contents)

                # Initialize collections for unique entities
                unique_imports = {}
                unique_functions = {}
                unique_classes = {}

                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{file}_chunk_{idx:06d}"
                    chunk_summary = summarize_file_chunk(chunk_text=chunk, file_name=file)
                    summary_embedding = get_embedding(chunk_summary)
                    chunk_embedding = get_embedding(chunk)

                    # Create the chunk node and link it to the file
                    self.kg.query("""
                        MERGE (chunk:Chunk {id: $chunk_id})
                        SET chunk.raw_code = $raw_code, 
                            chunk.summary = $summary, 
                            chunk.summary_embedding = $summary_embedding, 
                            chunk.chunk_embedding = $chunk_embedding
                        WITH chunk
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CONTAINS]->(chunk)
                    """, {
                        'chunk_id': chunk_id,
                        'raw_code': chunk,
                        'summary': chunk_summary,
                        'summary_embedding': summary_embedding,
                        'chunk_embedding': chunk_embedding,
                        'file_path': file
                    })

                    # Extract and process code entities for each chunk
                    chunk_entities = extract_code_entities(chunk)

                    # Collect unique imports
                    for imp in chunk_entities['imports']:
                        module_name = imp['module']
                        if module_name not in unique_imports:
                            unique_imports[module_name] = set(imp['entities'])
                        else:
                            unique_imports[module_name].update(imp['entities'])

                    # Collect unique functions
                    for func in chunk_entities['functions']:
                        func_name = func['name']
                        if func_name not in unique_functions:
                            unique_functions[func_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in func['parameters']]),
                                'return_type': func['return_type']
                            }

                    # Collect unique classes
                    for cls in chunk_entities['classes']:
                        cls_name = cls['name']
                        if cls_name not in unique_classes:
                            unique_classes[cls_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in cls['parameters']])
                            }

                # Store unique entities in the graph

                # Create and link unique import nodes
                for module, entities in unique_imports.items():
                    self.kg.query("""
                        MERGE (import:Import {module: $module})
                        SET import.entities = $entities
                        WITH import
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CALLS]->(import)
                    """, {
                        'module': module,
                        'entities': list(entities),
                        'file_path': file
                    })

                # Create and link unique function nodes
                for name, func in unique_functions.items():
                    self.kg.query("""
                        MERGE (function:Function {name: $name})
                        SET function.parameters = $parameters, function.return_type = $return_type
                        WITH function
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:DEFINES]->(function)
                    """, {
                        'name': name,
                        'parameters': func['parameters'],
                        'return_type': func['return_type'],
                        'file_path': file
                    })

                # Create and link unique class nodes
                for name, cls in unique_classes.items():
                    self.kg.query("""
                        MERGE (class:Class {name: $name})
                        SET class.parameters = $parameters
                        WITH class
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:DEFINES]->(class)
                    """, {
                        'name': name,
                        'parameters': cls['parameters'],
                        'file_path': file
                    })

                # Link all chunks in sequence using APOC's `NEXT` relationship
                self.kg.query("""
                    MATCH (file:File {path: $file_path})-[:CONTAINS]->(chunk:Chunk)
                    WITH chunk ORDER BY chunk.id ASC
                    WITH collect(chunk) AS chunks
                    CALL apoc.nodes.link(chunks, 'NEXT')
                    RETURN count(*)
                """, {
                    'file_path': file
                })

    def _find_files_without_summaries(self):
        """
        Find all files in the graph that do not have summaries.

        Returns:
            List[str]: A list of file paths that do not have summaries.
        """
        query = """
        MATCH (file:File)
        WHERE file.summary IS NULL
        RETURN file.path AS file_path
        """
        result = self.kg.query(query)
        return [record['file_path'] for record in result]

    def _find_directories_without_summaries(self):
        """
        Find all directories in the graph that do not have summaries.

        Returns:
            List[str]: A list of directory paths that do not have summaries.
        """
        query = """
        MATCH (dir:Directory)
        WHERE dir.summary IS NULL
        RETURN dir.path AS dir_path
        """
        result = self.kg.query(query)
        return [record['dir_path'] for record in result]
    
    def _find_nodes_without_embeddings(self):
        """
        Find all files and directories in the graph that have summaries but do not have embeddings.

        Returns:
            List[dict]: A list of dictionaries containing the node type ('File' or 'Directory') and the path.
        """
        query = """
        MATCH (n)
        WHERE n.summary IS NOT NULL AND n.summary_embedding IS NULL AND (n:File OR n:Directory)
        RETURN labels(n) AS node_type, n.path AS node_path
        """
        result = self.kg.query(query)
        return [{'node_type': record['node_type'][0], 'node_path': record['node_path']} for record in result]
    
    
    def _summarize_file_from_chunks(self, file_path):
        """
        Summarize a file based on the summaries of its chunks.

        Args:
            file_path (str): The path to the file to summarize.

        Returns:
            str: The summary of the file.
        """
        # Query to get summaries of all chunks associated with the file
        query = """
        MATCH (file:File {path: $file_path})-[:CONTAINS]->(chunk:Chunk)
        RETURN chunk.summary AS chunk_summary
        ORDER BY chunk.id ASC
        """
        result = self.kg.query(query, {'file_path': file_path})
        chunk_summaries = ['Chunk summaries'] + [record['chunk_summary'] for record in result]

        # Summarize the list of chunk summaries
        file_summary = summarize_list_of_summaries(chunk_summaries)

        # Store the file summary in the graph under the "summary" attribute
        self.kg.query("""
            MATCH (file:File {path: $file_path})
            SET file.summary = $file_summary
        """, {
            'file_path': file_path,
            'file_summary': file_summary
        })

        return file_summary
    
    def _summarize_directory(self, directory_path):
        """
        Summarize a directory based on the summaries of its files and subdirectories.

        Args:
            directory_path (str): The path to the directory to summarize.

        Returns:
            str: The summary of the directory.
        """
        # Query to get summaries of all files directly contained in the directory
        file_query = """
        MATCH (dir:Directory {path: $directory_path})-[:CONTAINS]->(file:File)
        RETURN file.summary AS file_summary
        """
        file_result = self.kg.query(file_query, {'directory_path': directory_path})
        file_summaries = [record['file_summary'] for record in file_result]

        # Query to get all subdirectories directly contained in the directory
        subdir_query = """
        MATCH (dir:Directory {path: $directory_path})-[:CONTAINS]->(subdir:Directory)
        RETURN subdir.path AS subdir_path
        """
        subdir_result = self.kg.query(subdir_query, {'directory_path': directory_path})
        subdir_paths = [record['subdir_path'] for record in subdir_result]

        # Recursively summarize each subdirectory if it doesn't already have a summary
        subdir_summaries = []
        for subdir_path in subdir_paths:
            subdir_summary = self._summarize_directory(subdir_path)
            subdir_summaries.append(subdir_summary)

        # Combine file summaries and subdirectory summaries
        all_summaries = ['File summaries: '] + file_summaries + ['Subdirectory summaries: ']  + subdir_summaries

        # Summarize the list of all summaries (files + subdirectories)
        directory_summary = summarize_list_of_summaries(all_summaries)

        # Store the directory summary in the graph under the "summary" attribute
        self.kg.query("""
            MATCH (dir:Directory {path: $directory_path})
            SET dir.summary = $directory_summary
        """, {
            'directory_path': directory_path,
            'directory_summary': directory_summary
        })

        return directory_summary

    def _automate_summarization(self):
        """
        Automate the summarization process for files and directories in the graph.
        """
        # Summarize files without summaries
        files_without_summaries = self._find_files_without_summaries()
        for file_path in tqdm(files_without_summaries, desc='Summarizing files'):
            self._summarize_file_from_chunks(file_path)

        # Summarize directories without summaries
        directories_without_summaries = self._find_directories_without_summaries()
        for dir_path in tqdm(directories_without_summaries, 'Summarizing directories'):
            self._summarize_directory(dir_path)

        # Generate embeddings for nodes that have summaries but no embeddings
        self._generate_and_store_embeddings()

    def _generate_and_store_embeddings(self):
        """
        Generate embeddings for files and directories that have summaries but lack embeddings.
        """
        nodes_without_embeddings = self._find_nodes_without_embeddings()

        for node in tqdm(nodes_without_embeddings, desc='Creating File and Directory embeddings'):
            # Retrieve the summary of the node
            query = f"""
            MATCH (n:{node['node_type']} {{path: $node_path}})
            RETURN n.summary AS summary
            """
            result = self.kg.query(query, {'node_path': node['node_path']})
            summary = result[0]['summary']

            # Generate the embedding for the summary
            embedding = get_embedding(summary)

            # Store the embedding back in the graph
            query = f"""
            MATCH (n:{node['node_type']} {{path: $node_path}})
            SET n.summary_embedding = $embedding
            """
            self.kg.query(query, {
                'node_path': node['node_path'],
                'embedding': embedding
            })

    def _create_vector_index(self, label, property_name="summary_embeddings", index_name=None, dimensions=1536):
        """
        Create a vector index for the specified label if it does not already exist.

        Args:
            label (str): The label of the nodes (e.g., 'File', 'Directory', 'Chunk').
            property_name (str): The property name on which the vector index is created. Default is 'summary_embeddings'.
            index_name (str): The name of the index. If None, it will default to 'labelVectorIndex'.
            dimensions (int): The dimensionality of the vectors. Default is 1536.
        """
        if not index_name:
            index_name = f"{label.lower()}VectorIndex"

        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label})
        ON n.{property_name}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        try:
            self.kg.query(query)
            print(f"Vector index {index_name} for label {label} created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the vector index: {e}")

    def _create_all_vector_indexes(self):
        """
        Create vector indexes for chunks, files, and directories. The indexes are separated for chunks and summaries.
        """
        # Create index for chunks
        self._create_vector_index(label="Chunk", property_name="chunk_embeddings", index_name="chunkRawVectorIndex")
        self._create_vector_index(label="Chunk", property_name="summary_embeddings", index_name="chunkSummaryVectorIndex")

        # Create index for files and directories
        self._create_vector_index(label="File", property_name="summary_embeddings", index_name="fileSummaryVectorIndex")
        self._create_vector_index(label="Directory", property_name="summary_embeddings", index_name="dirSummaryVectorIndex")




    def create_graph(self):

        self._load_dirs_and_files_to_graph()

        self._enrich_graph()

        self._automate_summarization()

        self._generate_and_store_embeddings()

        self._create_all_vector_indexes()



        
