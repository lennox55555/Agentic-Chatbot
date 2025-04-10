import json
import boto3
import logging
import requests
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# EC2 endpoint
EC2_ENDPOINT = "http://3.239.13.90:5000/process"

def lambda_handler(event, context):
    """Handle WebSocket events"""
    logger.info(f"Event received: {json.dumps(event)}")
    
    # extract connectionId
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
            # parse the message
            body = json.loads(event.get('body', '{}'))
            message = body.get('message', '')
            
            # determine whether to process in Lambda or send to EC2
            if len(message) > 10:
                # Route to EC2
                logger.info(f"Message length > 10, routing to EC2: {message}")
                
                # send request to EC2
                ec2_response = send_to_ec2(message)
                
                # send response back to client
                response_data = {
                    'response': ec2_response.get('response', f"Processed by EC2: {message}")
                }
            else:
                logger.info(f"Processing in Lambda: {message}")
                response_data = {
                    'response': f"Hi from Lambda. We got your message: \"{message}\""
                }
            
            # send response back to the client
            send_message_to_client(event, connection_id, response_data)
            
            return {'statusCode': 200}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {'statusCode': 500}
    
    else:
        logger.info(f"Unknown route: {route_key}")
        return {'statusCode': 400}

def send_message_to_client(event, connection_id, payload):
    """Send message back to the connected client"""
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    # create API Gateway management client
    api_client = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f"https://{domain}/{stage}"
    )
    
    # Send the message back to the client
    api_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(payload)
    )

def send_to_ec2(message):
    """Send a message to EC2 for processing via HTTP"""
    try:
        # prepare payload
        payload = {
            'message': message
        }
        
        # send HTTP request to EC2
        response = requests.post(
            EC2_ENDPOINT,
            json=payload,
            timeout=5  # 5 second timeout
        )
        
        # check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error from EC2: {response.status_code} - {response.text}")
            return {"response": f"Error processing on EC2: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error sending request to EC2: {str(e)}")
        return {"response": f"Error communicating with EC2: {str(e)}"}