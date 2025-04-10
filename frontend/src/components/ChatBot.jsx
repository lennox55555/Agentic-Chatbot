import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Row, Col, Form, Button, Card } from 'react-bootstrap';
import webSocketService from '../services/WebSocketService';

// Debug mode for additional logging
const DEBUG = true;

const ChatBot = () => {
  if (DEBUG) console.log('ChatBot component loaded');
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [hasSetupWebSocket, setHasSetupWebSocket] = useState(false);
  const messagesEndRef = useRef(null);
  const fallbackTimerRef = useRef(null);

  // Setup WebSocket event handlers
  const setupWebSocketHandlers = useCallback(() => {
    if (hasSetupWebSocket) return;
    
    if (DEBUG) console.log('Setting up WebSocket handlers');
    
    webSocketService.onConnectionChange((isConnected) => {
      if (DEBUG) console.log('WebSocket connection status changed:', isConnected);
      setConnectionStatus(isConnected ? 'Connected' : 'Disconnected');
    });
    
    webSocketService.onMessage((data) => {
      if (DEBUG) console.log('Message received from WebSocket:', data);
      
      // Clear any pending fallback timer
      if (fallbackTimerRef.current) {
        clearTimeout(fallbackTimerRef.current);
        fallbackTimerRef.current = null;
      }
      
      // Check for response field
      if (data && data.response) {
        const botMessage = {
          text: data.response,
          sender: 'bot',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
      } 
      // Check for error field
      else if (data && data.error) {
        const errorMessage = {
          text: `Error: ${data.error}`,
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
      }
      // Handle internal server error message format
      else if (data && data.message === "Internal server error") {
        const errorMessage = {
          text: "The server encountered an error processing your request. Please try again later.",
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
      }
      // Handle the raw data format (if JSON parsing failed)
      else if (data && data.raw) {
        try {
          // Try to parse the raw data as JSON
          const rawData = JSON.parse(data.raw);
          if (rawData && rawData.response) {
            const botMessage = {
              text: rawData.response,
              sender: 'bot',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, botMessage]);
            setIsLoading(false);
            return;
          }
        } catch (e) {
          if (DEBUG) console.log('Failed to parse raw data as JSON');
        }
        
        const botMessage = {
          text: "Received a response in an unexpected format.",
          sender: 'bot',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
        
        // Log the raw data for debugging
        if (DEBUG) console.warn("Raw data received:", data.raw);
      }
      // Fallback for unexpected message format
      else {
        if (DEBUG) console.warn("Received unexpected message format:", data);
        const botMessage = {
          text: "Received a response in an unexpected format.",
          sender: 'bot',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
      }
    });
    
    webSocketService.onError((error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('Connection Error');
      
      // Add an error message to the chat
      const errorMessage = {
        text: typeof error === 'string' ? error : 'Connection error occurred. Please try again later.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    });
    
    setHasSetupWebSocket(true);
  }, [hasSetupWebSocket]);

  // Connect to WebSocket on component mount
  useEffect(() => {
    if (DEBUG) console.log('ChatBot component mounted, initializing WebSocket');
    
    // Connect to WebSocket if not already connected
    if (!webSocketService.isConnected) {
      webSocketService.connect();
    }
    
    // Setup handlers
    setupWebSocketHandlers();
    
    // No need to disconnect on unmount - we want the WebSocket to stay alive
    return () => {
      if (DEBUG) console.log('ChatBot component unmounting, but keeping WebSocket alive');
      
      // Clear any pending fallback timer on unmount
      if (fallbackTimerRef.current) {
        clearTimeout(fallbackTimerRef.current);
        fallbackTimerRef.current = null;
      }
    };
  }, [setupWebSocketHandlers]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Send a message to the chatbot
  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to the chat
    const userMessage = { text: input, sender: 'user', timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    const sentMessage = input;
    setInput('');
    setIsLoading(true);

    // Send message via WebSocket
    if (DEBUG) console.log('Sending message via WebSocket:', sentMessage);
    webSocketService.sendMessage(sentMessage);
    
    // Set a fallback timer in case WebSocket response doesn't come back
    fallbackTimerRef.current = setTimeout(() => {
      if (DEBUG) console.log('No WebSocket response received within timeout, using fallback');
      
      // Only add the fallback message if we're still loading
      if (isLoading) {
        const botMessage = {
          text: `I apologize for the delay. It seems like the server is taking longer than expected to respond. Please try again in a moment.`,
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isWarning: true
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
      }
    }, 15000); // Increased timeout to 15 seconds for model processing
  };

  return (
    <Container className="py-5">
      <Row className="justify-content-center">
        <Col md={8}>
          <Card className="shadow">
            <Card.Header className="bg-primary text-white">
              <h4 className="mb-0">Duke Agentic ChatBot</h4>
              <small className="text-light">Status: {connectionStatus}</small>
            </Card.Header>
            <Card.Body className="chat-container bg-light" style={{ height: '400px', overflowY: 'auto' }}>
              {messages.length === 0 ? (
                <div className="text-center text-muted my-5">
                  <p>Ask me about Duke University's programs, events, and anything about the Duke AI Meng Program!</p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`mb-3 d-flex ${msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
                  >
                    <div
                      className={`p-3 rounded-3 ${
                        msg.sender === 'user'
                          ? 'bg-primary text-white'
                          : msg.isError
                          ? 'bg-danger text-white'
                          : msg.isWarning
                          ? 'bg-warning'
                          : 'bg-white border'
                      }`}
                      style={{ maxWidth: '80%' }}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="mb-3 d-flex justify-content-start">
                  <div className="p-3 rounded-3 bg-white border">
                    <div className="spinner-grow spinner-grow-sm text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>{' '}
                    Thinking...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </Card.Body>
            <Card.Footer className="bg-white">
              <Form onSubmit={sendMessage}>
                <Row>
                  <Col>
                    <Form.Control
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Type your message here..."
                      disabled={isLoading}
                    />
                  </Col>
                  <Col xs="auto">
                    <Button type="submit" variant="primary" disabled={isLoading || connectionStatus !== 'Connected'}>
                      {isLoading ? (
                        <>
                          <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                          <span className="visually-hidden">Loading...</span>
                        </>
                      ) : (
                        'Send'
                      )}
                    </Button>
                  </Col>
                </Row>
              </Form>
            </Card.Footer>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ChatBot;