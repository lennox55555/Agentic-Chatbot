// WebSocketService.js - Final Version with Debug Mode

// Create a singleton instance that persists across hot reloads
let serviceInstance = null;

// Debug mode for additional logging
const DEBUG = true;

class WebSocketService {
  constructor() {
    // If we already have an instance, return it
    if (serviceInstance) {
      if (DEBUG) console.log('Returning existing WebSocketService instance');
      return serviceInstance;
    }
    
    // Remove trailing slash from URL if present
    this.url = "wss://bvwq1y85ha.execute-api.us-east-1.amazonaws.com/prod";
    this.socket = null;
    this.isConnected = false;
    this.messageCallbacks = [];
    this.connectionCallbacks = [];
    this.errorCallbacks = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000; // Start with 3 seconds
    this.pendingMessages = [];
    
    // Store this instance
    serviceInstance = this;
    
    // Log the URL we're attempting to connect to
    if (DEBUG) console.log('WebSocket will connect to:', this.url);
    
    // Setup window event listeners to handle page lifecycle
    if (typeof window !== 'undefined') {
      // Try to gracefully close the connection when the page is unloaded
      window.addEventListener('beforeunload', () => {
        if (this.socket && this.isConnected) {
          if (DEBUG) console.log('Page is being unloaded, closing WebSocket');
          this.socket.close(1000, "Page unload");
        }
      });
    }
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      if (DEBUG) console.log('WebSocket already connected or connecting, skipping new connection');
      return;
    }
    
    if (DEBUG) console.log('Attempting to connect to WebSocket...');
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = () => {
        if (DEBUG) console.log('WebSocket connection established successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0; // Reset reconnect attempts on successful connection
        this.reconnectDelay = 3000; // Reset reconnect delay
        
        // Notify all connection callbacks
        this.connectionCallbacks.forEach(callback => callback(true));
        
        // Send any pending messages
        if (this.pendingMessages.length > 0) {
          if (DEBUG) console.log(`Sending ${this.pendingMessages.length} pending messages`);
          [...this.pendingMessages].forEach(message => {
            this.doSendMessage(message);
          });
          this.pendingMessages = [];
        }
      };
      
      this.socket.onmessage = (event) => {
        if (DEBUG) console.log('WebSocket raw message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          if (DEBUG) console.log('Parsed WebSocket message:', data);
          this.messageCallbacks.forEach(callback => callback(data));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          // Try to send the raw data even if parsing failed
          this.messageCallbacks.forEach(callback => callback({ 
            error: "Failed to parse response", 
            raw: event.data 
          }));
        }
      };
      
      this.socket.onclose = (event) => {
        if (DEBUG) console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
        this.isConnected = false;
        this.connectionCallbacks.forEach(callback => callback(false));
        
        // Don't reconnect if the connection was closed normally (1000 = normal closure, 1001 = going away)
        // or if max attempts reached
        if (event.code !== 1000 && event.code !== 1001 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000); // Max 30 seconds
          if (DEBUG) console.log(`Will attempt to reconnect in ${delay/1000} seconds... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('Maximum reconnect attempts reached. Please refresh the page.');
          this.errorCallbacks.forEach(callback => 
            callback(new Error('Maximum reconnect attempts reached. Please refresh the page.'))
          );
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error occurred:', error);
        this.errorCallbacks.forEach(callback => callback(error));
      };
    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      this.errorCallbacks.forEach(callback => callback(err));
    }
  }
  
  disconnect() {
    if (this.socket && this.isConnected) {
      if (DEBUG) console.log('Manually disconnecting WebSocket');
      this.socket.close(1000, "User initiated disconnect");
      this.isConnected = false;
    }
  }
  
  sendMessage(message) {
    if (DEBUG) console.log('Attempting to send message:', message);
    
    if (!this.isConnected) {
      if (DEBUG) console.log('WebSocket not connected, queuing message and connecting...');
      // Store message to send after connection
      if (!this.pendingMessages.includes(message)) {
        this.pendingMessages.push(message);
      }
      this.connect();
      return;
    }
    
    this.doSendMessage(message);
  }
  
  doSendMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const payload = JSON.stringify({
        action: 'sendMessage',
        message
      });
      if (DEBUG) console.log('Sending WebSocket message:', payload);
      this.socket.send(payload);
    } else {
      console.error('WebSocket is not connected or ready. ReadyState:', this.socket ? this.socket.readyState : 'no socket');
      // Queue the message for later sending if not already queued
      if (!this.pendingMessages.includes(message)) {
        this.pendingMessages.push(message);
      }
      
      // If the socket exists but is closing or closed, reconnect
      if (this.socket && (this.socket.readyState === WebSocket.CLOSING || this.socket.readyState === WebSocket.CLOSED)) {
        if (DEBUG) console.log('Socket is closing or closed, attempting to reconnect...');
        this.connect();
      }
    }
  }
  
  onMessage(callback) {
    // Remove any duplicate callbacks
    this.messageCallbacks = this.messageCallbacks.filter(cb => cb !== callback);
    this.messageCallbacks.push(callback);
  }
  
  onConnectionChange(callback) {
    // Remove any duplicate callbacks
    this.connectionCallbacks = this.connectionCallbacks.filter(cb => cb !== callback);
    this.connectionCallbacks.push(callback);
    
    // Immediately notify of current state
    callback(this.isConnected);
  }
  
  onError(callback) {
    // Remove any duplicate callbacks
    this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    this.errorCallbacks.push(callback);
  }
}

if (DEBUG) console.log('WebSocketService module loaded');
const webSocketService = new WebSocketService();
export default webSocketService;