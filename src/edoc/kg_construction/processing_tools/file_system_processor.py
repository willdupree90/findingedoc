import os
from datetime import datetime

from edoc.kg_construction.build_tools.utils import should_skip_file_or_dir

class FileSystemProcessor:
    def __init__(
            self, 
            root_directory 
    ):
        """
        Initialize the CodebaseGraph with a connection to Neo4j.

        Args:
            root_directory (str): The directory to be extracted into knowledge.
        """

        self.root_directory = root_directory
        
    def _get_file_info(self, file_path):
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

    def load_dirs_and_files_to_graph(self, kg):
        """
        Traverse a directory and create a graph in Neo4j representing the directory structure and file information.

        Args:
            kg (Neo4jGraph): graph object to complete cypher queries
        """
        print("Creating file and dir nodes from Walk")
        for root, dirs, files in os.walk(self.root_directory):

            dir_name = os.path.basename(root)
            # Create node for the directory
            if not should_skip_file_or_dir(root):
                kg.query(
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
                if not should_skip_file_or_dir(dir_path):
                    kg.query(
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
                file_info = self._get_file_info(file_path)
                if not should_skip_file_or_dir(file_path):
                    kg.query(
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