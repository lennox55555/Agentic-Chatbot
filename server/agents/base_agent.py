from langchain.agents import initialize_agent, AgentType
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
import os
import dotenv 

dotenv.load_dotenv()

class BaseAgent:
    """Base agent class for Duke University chatbot"""
    
    def __init__(self, tools=None, memory=None):
        """
        Initialize the base agent
        
        Args:
            tools: List of LangChain tools to use
            memory: Conversation memory to use
        """
        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=0.2,
            model_name="gpt-4o-mini",  # You can change to your preferred model
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize memory if not provided
        self.memory = memory or ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize tools
        self.tools = tools or []
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True
        )
    
    def process_query(self, query: str) -> str:
        """
        Process a user query
        
        Args:
            query: The user's query string
            
        Returns:
            The agent's response
        """
        return self.agent.run(query)