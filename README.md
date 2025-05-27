
# FindingEdoc
![Finding Edoc Banner](graph_banner.png)
In this project, we will use generative AI, knowledge graphs, and Retrieval-Augmented Generation (RAG) to help developers explore codebases via a chatbot.

## How to Use

### 1. Setting Up Your Environment

Before you can start  using the chatbot tool, you'll need to [set up your environment](#environment-setup). This includes obtaining necessary API keys and configuring environment variables.

Make sure you have Docker and Python set up as per the instructions provided later in the README (if not installed). This will involve:

- [Installing Docker](#docker-setup).
- [Setting up Python](#python-environment) and virtual environments via `envwrapper`.

### 2. Using Edoc for Code Question-Answer

Once your environment is set up, you can start using Edoc to perform code-related questions and answers through the chatbot interface.

#### 2.1 Run the Gradio Chatbot Interface via Docker (preferred)

Starting the docker service brings up the chatbot, via Gradio.

1. Open a terminal and navigate to the root directory of the project.

2. Start the Docker service with:
   ```bash
   docker-compose up
   ```
   This will set up the environment, including Neo4j and Python Gradio App.

3. You can access the Gradio app at [http://localhost:7860](http://localhost:7860). Gradio's `share=True` so the logs may display a sharable link as well.

#### 2.2 Using the Gradio Interface

The Gradio interface will provide several functionalities that allow you to upload graph data, set an API key, ask questions, and delete data from the knowledge graph.

- **Select an LLM Model**
   For both chat and graph creation you can select available models to interact with. The base model can be set via evironment variables (see [here](#environment-variables)). :warning: To alter the selectable models you must have access to them via API, as well as name them in `src\edoc\chatbot.py`. 

- **Set OpenAI API Key**: 
  If you haven’t already set the `OPENAI_API_KEY` in the `.env` file, the Gradio interface will prompt you to input your OpenAI API key before interacting with the chatbot. The key will only be stored during the session.
  
- **Upload Graph Data**: 
  Use the "Upload files" tab to input a zip of a coding project you want to explore. It is important the ZIP file contains a single root directory (top-level folder) that shares the ZIP's name. All other files, folders, and subdirectories are then placed inside that root directory.. The files will be processed, and the knowledge graph will be populated with the extracted information.

- **Ask Questions**: 
  Once the graph is populated with data, you can ask the chatbot questions about the codebase, such as file structure, function definitions, classes, and other key entities.

- **Delete Graph Data**: 
  If you need to delete the current knowledge graph data, navigate to the "Delete data" tab, enter the keyword `Delete`, and submit. This will clear all the nodes and relationships in the Neo4j database.

#### 2.3 Develop and explore locally via Neo4j Service and Python virtual environment

1. From a terminal in the root of the project start the Neo4j Docker service with:
   ```bash
   docker-compose up neo4j
   ```

2. Open a second terminal and activate your Python environment:
   ```bash
   workon your_env
   ```
3. Run the chatbot interface using the following command:
   ```bash
   python findingedoc/src/edoc/chatbot.py
   ```

4. Once the Gradio interface starts, a link to access the chatbot interface will be displayed in your terminal. Open this link in your browser to interact with the chatbot.

5. (Optional) Edit or execute any code via Jupyter Notebooks. Warning: if you make changes to the code base and want to re-run from Docker only again you will need to rebuild via
   ```bash
   docker-compose up --build
   ```
   This will ensure any changes to the source code are recognized within the containerized apps.


## Environment Setup

### Environment Variables

#### 1. Obtain an OpenAI API Key

1. Sign up for an OpenAI account if you don't have one.
2. Visit the OpenAI API page and create an API key.
3. Keep this key handy, as you'll need it in the next step.

#### 2. Create an `.env` File

In the root of your project, create a file named `.env` and add **all** of the following variables:

```dotenv
# ──────────────────────────────────────────────────────────────────────────────
# Neo4j credentials
# ──────────────────────────────────────────────────────────────────────────────
NEO4J_USERNAME=your_neo4j_username      # e.g. “neo4j”
NEO4J_PASSWORD=your_neo4j_password

# ──────────────────────────────────────────────────────────────────────────────
# OpenAI vs. Azure provider selection
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_PROVIDER=openai            # “openai” for public, “azure” for Azure OpenAI
LANGCHAIN_PROVIDER=langchain      # “langchain” for public, “azure-langchain” for Azure via LangChain

# ──────────────────────────────────────────────────────────────────────────────
# API Keys & Endpoints
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY=your_openai_api_key

# (Only required if OPENAI_PROVIDER=azure or LANGCHAIN_PROVIDER=azure-langchain)
AZURE_OPENAI_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=https://<your-azure-endpoint>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-06-01-preview

# ──────────────────────────────────────────────────────────────────────────────
# Model names
# ──────────────────────────────────────────────────────────────────────────────
LLM_MODEL=gpt-4o-mini             # Base model for Chat‐completion and graph summarization
EMBEDDING_MODEL=text-embedding-3-small  # Embedding model identifier
```

### Docker Setup

We will be using Docker to manage dependencies and run services like Neo4j, which is integral to the project.

#### Steps:

1. Install Docker if you haven't already.

2. Navigate to the root of the project.

3. Start the service by running `docker-compose up` from the command line. This will set up the environment, including Neo4j and Python Gradio App.

4. Once the service is up, access the Neo4j database at [http://localhost:7474](http://localhost:7474).

5. You can access the Gradio app at [http://localhost:7860](http://localhost:7860)

5. When finished, stop the service by running `ctr-c` and then `docker-compose down`.

### Local Python Environment

Set up the python code necessary to run the project on your local machine. The directions below are for `virtualenvwrapper` ([docs for Windows](https://pypi.org/project/virtualenvwrapper-win/)).

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
