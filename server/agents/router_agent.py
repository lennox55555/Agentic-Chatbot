from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
from agents.curriculum_agent import CurriculumAgent
from agents.locations_agent import LocationsAgent
from agents.events_agent import EventsAgent
from agents.base_agent import BaseAgent
import os 
import dotenv
import re

dotenv.load_dotenv()

class RouterAgent(BaseAgent):
    """Router agent that directs queries to the appropriate specialized agent"""
    
    def __init__(self, memory=None):
        """
        Initialize the router agent
        
        Args:
            memory: Conversation memory to use
        """
        # Initialize specialized agents (they'll share the same memory)
        self.memory = memory or ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.curriculum_agent = CurriculumAgent(memory=self.memory)
        self.locations_agent = LocationsAgent(memory=self.memory)
        self.events_agent = EventsAgent(memory=self.memory)
        
        # Create tools for the router
        self.tools = [
            Tool(
                name="Curriculum Information",
                func=self.curriculum_agent.process_query,
                description="Use this tool when the query is about courses, classes, majors, curriculum, academic programs, degrees, professors, or any academic information at Duke."
            ),
            Tool(
                name="Location Information",
                func=self.locations_agent.process_query,
                description="Use this tool when the query is about campus buildings, libraries, dining halls, dorms, directions, maps, facilities, or any physical locations at Duke."
            ),
            Tool(
                name="Event Information",
                func=self.events_agent.process_query,
                description="Use this tool when the query is about events, schedules, concerts, games, performances, club meetings, conferences, or any time-based activities at Duke."
            )
        ]
        
        # Initialize the router's LLM
        self.llm = ChatOpenAI(
            temperature=0,  # Low temperature for more deterministic routing
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create a prompt template for the router
        router_template = """
        You are a router for a Duke University information system. Your job is to analyze a user query and determine which specialized agent should handle it.
        
        The available agents are:
        1. Curriculum Information Agent: For queries about courses, classes, majors, academic programs, degrees, professors, or any academic information.
        2. Location Information Agent: For queries about campus buildings, libraries, dining halls, dorms, directions, maps, facilities, or any physical locations.
        3. Event Information Agent: For queries about events, schedules, concerts, games, performances, club meetings, conferences, or any time-based activities.
        
        Chat History:
        {chat_history}
        
        User Query: {query}
        
        Think about which agent or agents would be best suited to answer this query. If the query might require information from multiple domains, list all relevant agents.
        
        First, analyze the query and identify the key information needs.
        Then, determine which agent(s) would be most appropriate.
        
        Your response should be one of:
        - "curriculum": For purely academic/curriculum questions
        - "locations": For purely location-based questions
        - "events": For purely event-related questions
        - "curriculum,locations": For questions involving both curriculum and locations
        - "curriculum,events": For questions involving both curriculum and events
        - "locations,events": For questions involving both locations and events
        - "curriculum,locations,events": For complex questions that might involve all three domains

        Make sure that the responses would end in the following way ***agent_name*** for example if using one agent it would be
        ***curriculum*** or if using multiple agents it would be ***curriculum,locations***
        
        Agent(s):
        """
        
        self.router_prompt = PromptTemplate(
            input_variables=["chat_history", "query"],
            template=router_template
        )
        
        self.router_chain = LLMChain(
            llm=self.llm,
            prompt=self.router_prompt,
            verbose=True
        )
        
        # Call the parent constructor with our tools
        super().__init__(tools=self.tools, memory=self.memory)
    
    def route_query(self, query: str) -> str:
        """
        Route a query to the appropriate agent(s)
        
        Args:
            query: The user's query
            
        Returns:
            The routing decision
        """
        # Get chat history from memory
        chat_history = ""
        if hasattr(self.memory, "buffer"):
            chat_history = self.memory.buffer
        
        # Run the router chain
        response = self.router_chain.run(query=query, chat_history=chat_history)
        
        # Clean up response
        return response.strip().lower()
    
    def process_query(self, query: str) -> str:
        """
        Process a user query by routing to the appropriate agent(s)
        
        Args:
            query: The user's query
            
        Returns:
            The agent's response
        """
        # Get the routing decision
        routing = self.route_query(query)
        
        # Log the routing decision
        print(f"Router decision: {routing}")
        
        match = re.search(r"\*\*\*(.*?)\*\*\*", routing)
        if match:
            agents_str = match.group(1)
            routing = [agent.strip() for agent in agents_str.split(',')]
        
        # If multiple agents are needed, combine their responses
        if len(routing) > 1:
            agents_to_use = routing.split(",")
            responses = []
            
            for agent_name in agents_to_use:
                agent_name = agent_name.strip()
                
                if agent_name == "curriculum":
                    responses.append(f"[Curriculum Info] {self.curriculum_agent.process_query(query)}")
                elif agent_name == "locations":
                    responses.append(f"[Location Info] {self.locations_agent.process_query(query)}")
                elif agent_name == "events":
                    responses.append(f"[Event Info] {self.events_agent.process_query(query)}")
            
            # Combine responses using another LLM call to ensure coherence
            return self.combine_responses(query, responses)
        
        
        # Otherwise, route to a single agent
        if routing[0] == "curriculum":
            response = self.curriculum_agent.process_query(query)
            print('\n\nresponse from the curriculum agent: ', response)
            return response
        elif routing[0] == "locations":
            return self.locations_agent.process_query(query)
        elif routing[0] == "events":
            return self.events_agent.process_query(query)
        else:
            # Default to using the most appropriate agent based on keywords
            if any(word in query.lower() for word in ["class", "course", "major", "degree", "professor"]):
                return self.curriculum_agent.process_query(query)
            elif any(word in query.lower() for word in ["where", "building", "location", "dorm", "hall"]):
                return self.locations_agent.process_query(query)
            elif any(word in query.lower() for word in ["when", "event", "schedule", "game", "concert"]):
                return self.events_agent.process_query(query)
            else:
                # If still unsure, use the BaseAgent's process_query method
                return super().process_query(query)
    
    def combine_responses(self, query: str, responses: List[str]) -> str:
        """
        Combine responses from multiple agents into a coherent answer
        
        Args:
            query: The original user query
            responses: List of responses from different agents
            
        Returns:
            A coherent combined response
        """
        combine_template = """
        You need to combine information from multiple specialized agents to answer the user's query.
        
        User Query: {query}
        
        Agent Responses:
        {responses}
        
        Please synthesize this information into a single, coherent response that addresses all aspects of the user's query.
        Avoid redundancy and present the information in a natural, conversational way without mentioning that it came from different agents.
        """
        
        combine_prompt = PromptTemplate(
            input_variables=["query", "responses"],
            template=combine_template
        )
        
        combine_chain = LLMChain(
            llm=self.llm,
            prompt=combine_prompt
        )
        
        return combine_chain.run(query=query, responses="\n\n".join(responses))