# FindingEdoc
![Finding Edoc Banner](graph_banner.png)
In this project, we will use generative AI, knowledge graphs, and Retrieval-Augmented Generation (RAG) to help developers explore codebases via a chatbot.

## How to Use

Instructions on how to use the tool will be provided here as the project develops. Stay tuned for updates on scripts and commands that will facilitate interacting with the codebase through the chatbot.

## Environment Setup

### Docker Setup

We will be using Docker to manage dependencies and run services like Neo4j, which is integral to the project.

#### Steps:

1. Install Docker if you haven't already.

2. Navigate to the root of the project.

3. Start the service by running `docker-compose up` from the command line. This will set up the environment, including Neo4j.

4. Once the service is up, access the Neo4j database at [http://localhost:7474](http://localhost:7474).

5. When finished, stop the service by running `docker-compose down`.

### Python Environment

Set up the python code necessary to run the project.

#### Steps:

1. Create a virtual environment using the terminal.
   - We use Python 3.11 for this project.
   - `mkvirtualenv -p python3.11 your_env`

2. Activate and work on your environment using:
   - `workon your_env`

3. To install the necessary packages, including development dependencies, navigate to `src` and run:
   - `pip install -e .`

## Relevant Links and Resources

- [Neo4j Docker Image Documentation](https://hub.docker.com/_/neo4j)
- [Python 3.11 Documentation](https://docs.python.org/3.11/)
