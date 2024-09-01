from tqdm import tqdm
from edoc.kg_construction.summary_tools.utils import summarize_list_of_summaries
from edoc.gpt_helpers.gpt_basics import get_embedding

class SummaryManager:
    def __init__(
            self, 
            kg
    ):
        """
        Initialize the CodebaseGraph with a connection to Neo4j.

        Args:
            kg (Neo4jGraph): graph object to complete cypher queries
        """
        self.kg = kg
    
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

    def automate_summarization(self):
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