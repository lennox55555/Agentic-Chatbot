import json
import boto3
import logging
import requests
import os
import openai
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# eC2 endpoint
EC2_ENDPOINT = "ip address "

openai.api_key = os.environ.get("OPENAI_API_KEY")  

# list of inappropriate words/curse words to filter
INAPPROPRIATE_WORDS = [
    "ass", "asshole", "bitch", "bullshit", "crap", "damn", "dick", "fuck", "fucking", 
    "shit", "shitty", "piss", "pussy", "cock", "cunt", "whore", "slut", "bastard",
    "hell", "jerk", "idiot", "stupid", "dumb", "retard", "moron"
]

def lambda_handler(event, context):
    """Handle WebSocket events"""
    logger.info(f"Event received: {json.dumps(event)}")
    
    connection_id = event['requestContext']['connectionId']
    
    # handle different route keys/actions
    route_key = event['requestContext']['routeKey']
    
    if route_key == '$connect':
        logger.info(f"Client connected: {connection_id}")
        return {'statusCode': 200}
        
    elif route_key == '$disconnect':
        logger.info(f"Client disconnected: {connection_id}")
        return {'statusCode': 200}
        
    elif route_key == 'sendMessage':
        logger.info(f"Message received: {event.get('body', '')}")
        
        try:
            body = json.loads(event.get('body', '{}'))
            original_message = body.get('message', '')
            
            logger.info(f"Processing message content: '{original_message}'")
            
            if contains_inappropriate_content(original_message):
                logger.info(f"Message contains inappropriate content: '{original_message}'")
                response_data = {
                    'response': "I'm sorry, but I cannot process messages with inappropriate content. Please ensure your questions are appropriate."
                }
                send_message_to_client(event, connection_id, response_data)
                return {'statusCode': 200}
            
            if not is_duke_related(original_message):
                logger.info(f"Message determined as not related to Duke University")
                response_data = {
                    'response': "This message is unrelated to Duke University."
                }
                send_message_to_client(event, connection_id, response_data)
                return {'statusCode': 200}
            
            corrected_message = correct_grammar_with_openai(original_message)
            logger.info(f"Original: '{original_message}', Corrected: '{corrected_message}'")
            
            if corrected_message != original_message:
                logger.info("Corrections were made to the message")
                
                ec2_response = send_to_ec2(corrected_message)
                logger.info(f"EC2 response: {json.dumps(ec2_response)}")
                
                ec2_content = ec2_response.get('response', "")
                
                custom_response = f"I've corrected your message: '{original_message}' → '{corrected_message}'\n\nAnswer: {ec2_content.replace(f'Hi from EC2. Your message: \"{corrected_message}\"', '')}"
                
                response_data = {
                    'response': custom_response
                }
            else:
                logger.info("No corrections needed")
                
                ec2_response = send_to_ec2(original_message)
                logger.info(f"EC2 response: {json.dumps(ec2_response)}")
                
                response_data = ec2_response
            
            send_message_to_client(event, connection_id, response_data)
            logger.info(f"Response sent to client")
            
            return {'statusCode': 200}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response_data = {
                'response': f"Error processing your message: {str(e)}"
            }
            try:
                send_message_to_client(event, connection_id, response_data)
            except Exception as send_error:
                logger.error(f"Error sending error message to client: {str(send_error)}")
            return {'statusCode': 500}
    
    else:
        logger.info(f"Unknown route: {route_key}")
        return {'statusCode': 400}

def contains_inappropriate_content(message):
    """
    Check if the message contains inappropriate content like curse words.
    
    Returns:
        bool: True if inappropriate content found, False otherwise
    """
    if not message:
        return False
        
    message_lower = message.lower()
    
    # check for exact curse words or variations
    for word in INAPPROPRIATE_WORDS:
        # Check for the word as a whole word, not as part of another word
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, message_lower):
            logger.info(f"Inappropriate word found: '{word}'")
            return True
    
    try:
        return check_inappropriate_with_openai(message)
    except Exception as e:
        logger.error(f"Error checking inappropriate content with OpenAI: {str(e)}")
        return False

def check_inappropriate_with_openai(message):
    """
    Check if the message contains inappropriate content using OpenAI API.
    
    Returns:
        bool: True if inappropriate content found, False otherwise
    """
    try:
        logger.info(f"Checking inappropriate content with OpenAI: '{message}'")
        
        system_message = """
        Your task is to determine if the message contains inappropriate content (profanity, offensive language, adult content, etc.).
        
        Respond with ONLY ONE of these two values:
        - "INAPPROPRIATE" - if the message contains inappropriate content
        - "APPROPRIATE" - if the message does not contain inappropriate content
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Analyze this message: \"{message}\""}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip().upper()
        logger.info(f"OpenAI API inappropriate check response: '{result_text}'")
        
        is_inappropriate = "INAPPROPRIATE" in result_text
        
        logger.info(f"Message inappropriate determination: is_inappropriate={is_inappropriate}")
        
        return is_inappropriate
        
    except Exception as e:
        logger.error(f"Error in check_inappropriate_with_openai: {str(e)}")
        return False

def is_duke_related(message):
    """
    Check if the message is related to Duke University.
    Uses simple keyword matching first, then OpenAI API if needed.
    
    Returns:
        bool: True if related to Duke University, False otherwise
    """
    if not message:
        return False
        
    message_lower = message.lower()
    
    duke_keywords = ['duke', 'university', 'blue devils', 'durham', 'chapel hill']
    
    for keyword in duke_keywords:
        if keyword in message_lower:
            logger.info(f"Message contains keyword '{keyword}', determined as Duke-related")
            return True
    
    try:
        return check_duke_relevance_with_openai(message)
    except Exception as e:
        logger.error(f"Error checking Duke relevance with OpenAI: {str(e)}")
        return True

def check_duke_relevance_with_openai(message):
    """
    Check if the message is related to Duke University using OpenAI API.
    
    Returns:
        bool: True if related to Duke University, False otherwise
    """
    try:
        logger.info(f"Checking Duke relevance with OpenAI: '{message}'")
        
        system_message = """
        You are an assistant for Duke University. Your task is to determine if the message is related to Duke University (academics, campus life, admissions, faculty, sports, etc.).
        
        Respond with ONLY ONE of these two values:
        - "RELATED" - if the message is related to Duke University
        - "UNRELATED" - if the message is not related to Duke University
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Analyze this message: \"{message}\""}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip().upper()
        logger.info(f"OpenAI API relevance response: '{result_text}'")
        
        is_related = "RELATED" in result_text
        
        logger.info(f"Message relevance determination: is_related={is_related}")
        
        return is_related
        
    except Exception as e:
        logger.error(f"Error in check_duke_relevance_with_openai: {str(e)}")
        return True

def correct_grammar_with_openai(message):
    """
    Correct grammar and spelling using OpenAI API.
    
    Returns:
        str: Corrected message
    """
    if not message or len(message.strip()) < 3:
        return message
        
    try:
        logger.info(f"Correcting grammar with OpenAI: '{message}'")
        
        system_message = """
        You are an expert editor. Your task is to correct any spelling or grammatical errors in the user's message.
        
        If the message contains errors, fix them and return the corrected version.
        If the message is already correct, return it exactly as is.
        
        Your response should ONLY be the corrected message, with no explanations or additional text.
        Keep the meaning and intent exactly the same, just fix any errors.
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Correct this message: \"{message}\""}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        corrected_message = response.choices[0].message.content.strip()
        logger.info(f"OpenAI API correction response: '{corrected_message}'")
        
        if not corrected_message:
            logger.warning("Correction returned empty result, using original message")
            return message
            
        return corrected_message
        
    except Exception as e:
        logger.error(f"Error in correct_grammar_with_openai: {str(e)}")
        return message

def send_message_to_client(event, connection_id, payload):
    """Send message back to the connected client"""
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    logger.info(f"Preparing to send message to client {connection_id}")
    
    api_client = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f"https://{domain}/{stage}"
    )
    
    api_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(payload)
    )
    
    logger.info(f"Message sent to client: {json.dumps(payload)}")

def send_to_ec2(message):
    """Send a message to EC2 for processing via HTTP"""
    try:
        logger.info(f"Sending message to EC2: '{message}'")
        
        payload = {
            'message': message
        }
        
        response = requests.post(
            EC2_ENDPOINT,
            json=payload,
            timeout=180  
        )
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Successful response from EC2: {json.dumps(response_data)}")
            return response_data
        else:
            error_message = f"Error from EC2: {response.status_code} - {response.text}"
            logger.error(error_message)
            return {"response": f"Error processing on EC2: {response.status_code}"}
    except Exception as e:
        error_message = f"Error sending request to EC2: {str(e)}"
        logger.error(error_message)
        return {"response": f"Error communicating with EC2: {str(e)}"}