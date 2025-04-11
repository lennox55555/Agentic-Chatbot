from agents.base_agent import BaseAgent
from tools.duke_api_tools import get_location_tools
from langchain.chains.conversation.memory import ConversationBufferMemory

class LocationsAgent(BaseAgent):
    """Agent specialized for Duke location-related queries"""
    
    def __init__(self, memory=None):
        """
        Initialize a locations agent with appropriate tools
        
        Args:
            memory: Optional conversation memory
        """
        # Get location tools
        location_tools = get_location_tools()
        
        # Initialize the base agent with location tools
        super().__init__(tools=location_tools, memory=memory)
        
        # Add Duke University-specific system message for locations
        system_message = """
        You are an AI assistant for Duke University, helping students and visitors navigate Duke's campuses and locations.
        Your primary responsibility is to provide accurate information about Duke's buildings, dining locations, facilities, and other places across campus.
        
        Duke University has several campus areas including:
        - West Campus (main campus with Gothic architecture)
        - East Campus (freshman campus with Georgian architecture)
        - Central Campus (connecting area with administrative buildings)
        
        Always be informative, helpful, and concise in your responses.
        When you don't know the answer, suggest consulting Duke's official resources or contacting the appropriate department.
        """
        
        # Update agent with system message
        self.agent.agent.llm_chain.prompt.messages[0].prompt.template = system_message

    def query(self, query_text, use_tools=True):
        """
        Process a location-related query.
        
        Args:
            query_text: The user's query about Duke locations
            use_tools: Whether to use the location tools
            
        Returns:
            The agent's response
        """
        # You can add pre-processing or post-processing specific to location queries here
        response = super().query(query_text, use_tools=use_tools)
        return response