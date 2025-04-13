# Agentic-Chatbot

## Project Description 
This project is a full-stack web app that implements an Agentic AI Chatbot for Duke University. The chatbot is able to answer different questions about Duke's curriculum, events, and locations on campus. The front-end is implemented with React + Vite, while the backend is implemented with Flask. The backend is hosted on an EC2 Instance and receives queries from the frontend via a web socket that passes messages to the EC2 through Lambda functions. The backend utilizes LangChain to implement an agentic workflow and uses GPT-4o-mini as the LLM for the agents to process the queries. 

This chatbot is designed for incoming duke students or students considering applying to Duke University. Furthermore, the chatbot is meant to have a friendly and helpful tone that helps users retrieve the information they are looking for. Given that we students in the Duke AIPI program, the chatbot is more oriented towards answering questions about our program, but is able to answer questions about other programs and courses as well. 

## Project Structure 

```
Agentic-Chatbot/
├── evaluation/
│   ├── eval.py                  # Evaluation logic for the chatbot
│   ├── llm_eval_results.csv     # Results of language model evaluations
│   ├── visualization.py         # Scripts for visualizing evaluation results
├── frontend/                    # frontend repo for the REACT app 
├── server/
│   ├── agents/
│   │   ├── __init__.py          # Initialization for the agents module
│   │   ├── base_agent.py        # Base class for chatbot agents
│   │   ├── curriculum_agent.py  # Agent handling curriculum-related tasks (Duke Curriculum API)
│   │   ├── events_agent.py      # Agent managing event-related queries (Duke Events API)
│   │   ├── locations_agent.py   # Agent for location-based queries (Duke Places API)
│   │   ├── router_agent.py      # Router agent that implements routing logic between different agents
│   ├── data/
│   │   └── metadata/
│   │       └── subjects.json    # Metadata file containing subject information
│   ├── services/
│       ├── duke_api_service/
│            └── __init__.py   
│            └── base.py         # Base API class (reusable code across all Duke APIs)
│            └── curriculum.py   # Class implementing calls to the Duke curriculum API routes
│            └── events.py       # Class implementing calls to the Duke events API routes
│            └── places.py       # Class implementing calls to the Duke places API routes
│       ├── __init__.py      # Initialization for Duke API services
│       ├── pinecone_services.py  # Integration with Pinecone vector database
│       ├── query_service.py      # Service handling query operations (synchronously)
│       ├── webscraping_service.py # Service for web scraping operations (executed locally)
│       ├── tools/
│           ├── __init__.py           
│           ├── duke_api_tools.py  # Script implementing the tools used by agents (using the Duke API)
│   ├── app.py                   #  Main application logic (entry point of the EC2)
│   ├── lambda_handler.py        # Code that goes in the AWS Lambda
├── test/                        # Directory for test cases (if applicable)
├── .gitignore                   # Git ignore file specifying untracked files
├── LICENSE                      # License file for the project
├── README.md                    # Documentation file (this file)
├── requirements.txt             # Python dependencies for the project
├── upload_to_pinecone.py        # Script to upload data to Pinecone vector database (done locally)
```

## System architecture 

## Modeling Decisions 

Modeling decisions (architecture? fine-tuning? RAG? Agentic framework?)
"https://masters.pratt.duke.edu/",
"https://gradschool.duke.edu/academics/",
"https://admissions.duke.edu/academic-possibilities/"
"https://wikipedia.com

## Performance Evaluation 

## Approach to Cost Minimization 

Functional user interface

•
10-minute max video

–
Data sources and data collection/access

–
System architecture

–


–
Performance evaluation

–
Cost estimations / approach to cost minimization
