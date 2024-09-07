from edoc.gpt_helpers.connect import connect_to_neo4j
from edoc.rag_components.structured_retrievers import dir_file_structured_retriever

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

class BuildResponse:
    def __init__(self, model='gpt-4o-mini'):
        """
        Initialize CodebaseQA class with an LLM model and a Neo4j connection.

        Args:
            llm_model (str): The language model to use. Default is 'gpt-4o-mini'.

        """
        self.llm = ChatOpenAI(
            temperature=0,
            model=model
        )

        # Connect to Neo4j database
        self.kg = connect_to_neo4j()

        # Initialize chain
        self.chain = self.setup_chain()


    def setup_chain(self, structured_retriever=dir_file_structured_retriever):
        """
        Set up the prompt, template, and processing chain for answering questions.

        Args:
            structured_retriever (callable): A structured retriever to fetch context from the knowledge graph.
        """

        template = """Answer the question using the following context, if you are unsure say so:
        {context}

        Question: {question}

        Use natural language and be concise.

        Answer:"""


        prompt = ChatPromptTemplate.from_template(template)

        # Define the chain with the retriever and LLM
        chain = (
            RunnableParallel(
                {
                    "context": RunnablePassthrough() | structured_retriever,
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain

    def get_response(self, question, top_k=1):
        """
        Get the response by invoking the chain with the question and relevant context.

        Args:
            question (str): The user's question.
            top_k (int): The number of top results to consider. Default is 1.

        Returns:
            str: The generated answer from the LLM.
        """

        # Invoke the chain with the question and knowledge graph connection
        final_response = self.chain.invoke(
            {
                "question": question,
                "kg": self.kg,
                "top_k": top_k,
            }
        )
        return final_response
