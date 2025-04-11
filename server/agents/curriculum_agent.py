from agents.base_agent import BaseAgent
from tools.duke_api_tools import get_curriculum_tools
from langchain.chains.conversation.memory import ConversationBufferMemory

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