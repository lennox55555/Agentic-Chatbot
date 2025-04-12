import os
from agents.base_agent import BaseAgent
from tools.duke_api_tools import get_curriculum_tools
from langchain.chains.conversation.memory import ConversationBufferMemory
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

PINECONE = os.getenv("PINECONE_API_KEY")
ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
INDEX_NAME = os.getenv("PINECONE_INDEX", "agenticchatbotdb")

pc = Pinecone(api_key=PINECONE)

class CurriculumAgent(BaseAgent):
    """Agent specialized for curriculum-related queries"""
    
    def __init__(self, memory=None):
        """
        Initialize a curriculum agent with appropriate tools
        
        Args:
            memory: Optional conversation memory
        """
        # Get curriculum tools
        curriculum_tools = get_curriculum_tools()

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.index = pc.Index(INDEX_NAME)
        
        # Initialize the base agent with curriculum tools
        super().__init__(tools=curriculum_tools, memory=memory)
        
        # Add Duke University-specific system message
        system_message = """
        You are an AI assistant for Duke University, helping incoming students and students considering applying to Duke with curriculum-related queries.
        Your primary responsibility is to provide accurate information about Duke's courses, departments, and academic offerings.
        Always be informative, helpful, and concise in your responses.
        When you don't know the answer, suggest consulting Duke's official resources or contacting the appropriate department.
        """
        
        # Update agent with system message
        # Note: This is a simplified approach; you may need to adjust based on your LangChain version
        self.agent.agent.llm_chain.prompt.messages[0].prompt.template = system_message

    def embed_text(self, text: str) -> list:
        response = self.client.embeddings.create(
            input=[text],
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    
    def retrieve_context(self, query, top_k = 3):
        embedding = self.embed_text(query)
        response = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=os.getenv("PINECONE_NAMESPACE", "ns1")
        )

        contents = []
        for match in response["matches"]:
            rel_path = match["metadata"].get("file_path")
            if rel_path:
                agent_dir = Path(__file__).resolve().parent
                abs_path = (agent_dir / rel_path).resolve()

                if abs_path.exists():
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            contents.append(f.read())
                    except Exception as e:
                        print(f"[ERROR] Reading {abs_path}: {e}")
                else:
                    print(f"[WARN] File not found: {abs_path}")

        return contents
    
    def process_query(self, query: str) -> str:
        contexts = self.retrieve_context(query)
        context_str = "\n\n".join(contexts)

        prompt = f"""
        Below is relevant context retrieved from a vector database. Use this to help answer the user's question.

        User Query:
        {query}

        Context:
        {context_str}

        Answer:
        """
        
        return self.llm.predict(prompt)