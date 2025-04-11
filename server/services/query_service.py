from agents.router_agent import RouterAgent
from langchain.chains.conversation.memory import ConversationBufferMemory

class QueryService:
    """Service for processing user queries"""
    
    def __init__(self):
        """Initialize the query service with session management"""
        self.sessions = {}  # Store session memories
        self.agents = {}  # Store agents for each session
    
    def get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """
        Get or create a memory for a session
        
        Args:
            session_id: The user's session ID
            
        Returns:
            A conversation memory for the session
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        return self.sessions[session_id]
    
    def get_or_create_agent(self, session_id: str) -> RouterAgent:
        """
        Get or create a router agent for a session
        
        Args:
            session_id: The user's session ID
            
        Returns:
            A router agent for the session
        """
        if session_id not in self.agents:
            memory = self.get_or_create_memory(session_id)
            self.agents[session_id] = RouterAgent(memory=memory)
        return self.agents[session_id]
    
    def process_query(self, query: str, session_id: str = "default") -> str:
        """
        Process a user query
        
        Args:
            query: The user's query
            session_id: The user's session ID
            
        Returns:
            The agent's response
        """
        # Get or create the router agent for this session
        agent = self.get_or_create_agent(session_id)
        
        # Create a curriculum agent with the session memory
        # TODO: IMPLEMENT THE CODE FOR CHOOSING WHICH TOOL TO USE
        # agent = LocationsAgent(memory=memory)
        # agent = CurriculumAgent(memory=memory)
        # agent = EventsAgent(memory=memory)
        # print('\nProcessing query here!!!')
        print('\nProcessing query through router agent...')
        
        # Process the query through the router agent
        return agent.process_query(query)