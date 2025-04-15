"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import MessageList from "../../components/MessageList/MessageList";
import ChatInput from "../../components/ChatInput/ChatInput";
import styles from "./ChatInterface.module.css";

// WebSocket service
const createWebSocketService = () => {
  let serviceInstance = null;
  const DEBUG = true;

  class WebSocketService {
    constructor() {
      if (serviceInstance) {
        if (DEBUG) console.log("Returning existing WebSocket service instance");
        return serviceInstance;
      }
      this.url = "wss://37gj7ea8l3.execute-api.us-east-1.amazonaws.com/prod/";
      this.socket = null;
      this.isConnected = false;
      this.messageCallbacks = [];
      this.connectionCallbacks = [];
      this.errorCallbacks = [];
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 5;
      this.reconnectDelay = 3000;
      this.pendingMessages = [];
      serviceInstance = this;
      if (DEBUG) console.log("WebSocket will connect to:", this.url);
      if (typeof window !== "undefined") {
        window.addEventListener("beforeunload", () => {
          if (this.socket && this.isConnected) {
            if (DEBUG) console.log("Page is being unloaded, closing websocket");
            this.socket.close(1000, "page unload");
          }
        });
      }
    }

    connect() {
      if (
        this.socket &&
        (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)
      ) {
        if (DEBUG) console.log("WebSocket already connected or connecting, skipping new connection");
        return;
      }
      if (DEBUG) console.log("Attempting to connect to WebSocket...");
      try {
        this.socket = new WebSocket(this.url);
        this.socket.onopen = () => {
          if (DEBUG) console.log("WebSocket connection established successfully");
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 3000;
          this.connectionCallbacks.forEach((cb) => cb(true));
          if (this.pendingMessages.length > 0) {
            if (DEBUG) console.log(`Sending ${this.pendingMessages.length} pending messages`);
            [...this.pendingMessages].forEach((message) => {
              this.doSendMessage(message);
            });
            this.pendingMessages = [];
          }
        };
        this.socket.onmessage = (event) => {
          if (DEBUG) console.log("WebSocket raw message received:", event.data);
          
          // Skip empty messages
          if (!event.data || event.data.trim() === "") {
            if (DEBUG) console.log("Received empty message, ignoring");
            return;
          }
          
          try {
            const data = JSON.parse(event.data);
            if (DEBUG) console.log("Parsed WebSocket message:", data);
            this.messageCallbacks.forEach((cb) => cb(data));
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
            this.messageCallbacks.forEach((cb) =>
              cb({
                error: "failed to parse response",
                raw: event.data,
              })
            );
          }
        };
        this.socket.onclose = (event) => {
          if (DEBUG) console.log("WebSocket disconnected. code:", event.code, "reason:", event.reason);
          this.isConnected = false;
          this.connectionCallbacks.forEach((cb) => cb(false));
          if (event.code !== 1000 && event.code !== 1001 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000);
            if (DEBUG)
              console.log(
                `Will attempt to reconnect in ${delay / 1000} seconds... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
              );
            setTimeout(() => this.connect(), delay);
          } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("Maximum reconnect attempts reached. Please refresh the page.");
            this.errorCallbacks.forEach((cb) =>
              cb(new Error("Maximum reconnect attempts reached. Please refresh the page."))
            );
          }
        };
        this.socket.onerror = (error) => {
          console.error("WebSocket error occurred:", error);
          this.errorCallbacks.forEach((cb) => cb(error));
        };
      } catch (err) {
        console.error("Error creating WebSocket connection:", err);
        this.errorCallbacks.forEach((cb) => cb(err));
      }
    }

    disconnect() {
      if (this.socket && this.isConnected) {
        if (DEBUG) console.log("Manually disconnecting WebSocket");
        this.socket.close(1000, "user initiated disconnect");
        this.isConnected = false;
      }
    }

    // Simplified to just send a message
    sendMessage(message) {
      if (DEBUG) console.log('Attempting to send message:', message);
      
      if (!this.isConnected) {
        if (DEBUG) console.log("WebSocket not connected, queuing message and connecting...");
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
        // Simplified payload - no model_type
        const payload = JSON.stringify({
          action: "sendMessage",
          message
        });
        if (DEBUG) console.log("Sending WebSocket message:", payload);
        this.socket.send(payload);
      } else {
        console.error("WebSocket is not connected or ready. Readystate:", this.socket ? this.socket.readyState : "no socket");
        if (!this.pendingMessages.includes(message)) {
          this.pendingMessages.push(message);
        }
        
        if (this.socket && (this.socket.readyState === WebSocket.CLOSING || this.socket.readyState === WebSocket.CLOSED)) {
          if (DEBUG) console.log("Socket is closing or closed, attempting to reconnect...");
          this.connect();
        }
      }
    }

    onMessage(callback) {
      this.messageCallbacks = this.messageCallbacks.filter((cb) => cb !== callback);
      this.messageCallbacks.push(callback);
    }

    onConnectionChange(callback) {
      this.connectionCallbacks = this.connectionCallbacks.filter((cb) => cb !== callback);
      this.connectionCallbacks.push(callback);
      callback(this.isConnected);
    }

    onError(callback) {
      this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
      this.errorCallbacks.push(callback);
    }
  }

  return new WebSocketService();
};

const webSocketService = createWebSocketService();

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("Connecting...");
  // Removed selectedModel state
  const fallbackTimerRef = useRef(null);
  const lastMessageRef = useRef(null); // Track the last processed message ID

  const setupWebSocketHandlers = useCallback(() => {
    webSocketService.onConnectionChange((isConnected) => {
      setConnectionStatus(isConnected ? "Connected" : "Disconnected");
    });

    webSocketService.onMessage((data) => {
      if (fallbackTimerRef.current) {
        clearTimeout(fallbackTimerRef.current);
        fallbackTimerRef.current = null;
      }

      if (data && data.response) {
        // Standard response format (original)
        const messageId = Date.now() + 1;
        setMessages((prev) => {
          if (prev.some((msg) => msg.content === data.response && msg.id === lastMessageRef.current)) {
            return prev; // Skip if duplicate
          }
          const aiMessage = { id: messageId, content: data.response, role: "assistant" };
          lastMessageRef.current = messageId;
          return [...prev, aiMessage];
        });
        setIsLoading(false);
      } else if (data && data.message) {
        // Handling the new Lambda format that uses 'message' field
        const messageId = Date.now() + 1;
        setMessages((prev) => {
          if (prev.some((msg) => msg.content === data.message && msg.id === lastMessageRef.current)) {
            return prev; // Skip if duplicate
          }
          const aiMessage = { id: messageId, content: data.message, role: "assistant" };
          lastMessageRef.current = messageId;
          return [...prev, aiMessage];
        });
        setIsLoading(false);
      } else if (data && data.error) {
        const errorMessage = { id: Date.now() + 1, content: `Error: ${data.error}`, role: "assistant", isError: true };
        setMessages((prev) => [...prev, errorMessage]);
        setIsLoading(false);
      } else {
        const botMessage = { id: Date.now() + 1, content: "Received an unexpected response format.", role: "assistant" };
        setMessages((prev) => [...prev, botMessage]);
        setIsLoading(false);
      }
    });

    webSocketService.onError((error) => {
      setConnectionStatus("Connection Error");
      const errorMessage = {
        id: Date.now() + 1,
        content: typeof error === "string" ? error : "Connection error occurred. Please try again later.",
        role: "assistant",
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!webSocketService.isConnected) {
      webSocketService.connect();
    }
    setupWebSocketHandlers();
    return () => {};
  }, [setupWebSocketHandlers]);

  const handleSendMessage = (messageText) => {
    if (!messageText.trim()) return;
    const userMessage = { id: Date.now(), content: messageText, role: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    // Call sendMessage with just the message text
    webSocketService.sendMessage(messageText);
    fallbackTimerRef.current = setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        content: "I apologize for the delay. Please try again shortly.",
        role: "assistant",
        isWarning: true,
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 20000);
  };

  return (
    <div className={styles.container}>
      {/* Duke Logo and Name */}
      <div className={styles.dukeLogo}>
        <label>Duke University</label>
      </div>
      
      {/* Chat container */}
      <div className={styles.chatContainer}>
        <h1 className={styles.heading}>Duke BlueAgent</h1>
        <div className={styles.messageArea}>
          <MessageList messages={messages} isLoading={isLoading} />
          {isLoading}
        </div>
        <div className={styles.inputArea}>
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          <div className={styles.quickActions}></div>
        </div>
      </div>
    
      {/* Top right buttons */}
      <div className={styles.topRightButtons}>
        <a 
          href="https://github.com/lennox55555/Agentic-Chatbot" 
          target="_blank" 
          rel="noopener noreferrer" 
          className={styles.topButton}
          title="View on GitHub"
        >
          <i className="bi bi-github"></i>
        </a>
      </div>
    </div>
  );
};

export default ChatInterface;