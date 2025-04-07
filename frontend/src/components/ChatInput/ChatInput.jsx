"use client";

import { useState, useRef, useEffect } from "react";
import { Plus, Mic, Send } from "lucide-react";
import styles from "./ChatInput.module.css";

const ChatInput = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState("");
  const [placeholderText, setPlaceholderText] = useState("");
  const [speechError, setSpeechError] = useState("");
  const [isRecording, setIsRecording] = useState(false); // Track recording state
  const textareaRef = useRef(null);
  const animationRef = useRef(null);
  const recognitionRef = useRef(null);
  const animationState = useRef({
    questionIndex: 0,
    charIndex: 0,
    phase: "typing",
  });

  const questions = [
    "Where is Duke University located?",
    "How many students are enrolled at Duke?",
    "How much does the Duke AI MEng program cost?",
    "What is the average salary of a Duke graduate?",
    "What is the acceptance rate for Duke?"
  ];

  // Auto-resize the textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Typewriter effect
  useEffect(() => {
    if (input.length > 0) {
      setPlaceholderText("");
      if (animationRef.current) clearTimeout(animationRef.current);
      return;
    }

    const animate = () => {
      if (input.length > 0) return;

      const state = animationState.current;
      const currentQuestion = questions[state.questionIndex];

      if (state.phase === "typing") {
        if (state.charIndex < currentQuestion.length) {
          const newText = currentQuestion.slice(0, state.charIndex + 1);
          setTimeout(() => setPlaceholderText(newText), 10);
          state.charIndex++;
          animationRef.current = setTimeout(animate, 300);
        } else {
          state.phase = "pausing";
          animationRef.current = setTimeout(animate, 4000);
        }
      } else if (state.phase === "pausing") {
        state.phase = "deleting";
        animationRef.current = setTimeout(animate, 0);
      } else if (state.phase === "deleting") {
        if (state.charIndex > 0) {
          const newText = currentQuestion.slice(0, state.charIndex - 1);
          setTimeout(() => setPlaceholderText(newText), 10);
          state.charIndex--;
          animationRef.current = setTimeout(animate, 250);
        } else {
          state.phase = "typing";
          state.questionIndex = (state.questionIndex + 1) % questions.length;
          animationRef.current = setTimeout(animate, 2000);
        }
      }
    };

    animate();

    return () => {
      if (animationRef.current) clearTimeout(animationRef.current);
    };
  }, [input, questions]);

  // Initialize SpeechRecognition
  useEffect(() => {
    if (!("SpeechRecognition" in window) && !("webkitSpeechRecognition" in window)) {
      console.log("Speech recognition not supported in this browser.");
      setSpeechError("Speech recognition is not supported in your browser. Try using Chrome or Edge.");
      return;
    }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setIsRecording(true); // Show red dot
      console.log("Speech recognition started.");
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      console.log("Transcription:", transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setSpeechError(`Speech recognition failed: ${event.error}`);
      setIsRecording(false); // Reset to mic icon
    };

    recognition.onend = () => {
      setIsRecording(false); // Back to mic icon
      console.log("Speech recognition ended.");
      setSpeechError("");
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Handle microphone button click
  const handleMicClick = () => {
    if (recognitionRef.current) {
      if (input.length > 0) setInput("");
      setPlaceholderText("");
      if (animationRef.current) clearTimeout(animationRef.current);
      recognitionRef.current.start();
    } else {
      setSpeechError("Speech recognition is not available. Please use Chrome or Edge.");
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    onSendMessage(input);
    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.inputContainer}>

        <textarea
          ref={textareaRef}
          className={styles.input}
          placeholder={placeholderText || "Ask anything"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.iconButton}
            onClick={handleMicClick}
            disabled={isLoading}
          >
            {isRecording ? (
              <span className={styles.recordingDot}></span>
            ) : (
              <Mic size={20} />
            )}
          </button>
          {input.trim() && (
            <button type="submit" className={styles.iconButton} disabled={isLoading}>
              <Send size={20} />
            </button>
          )}
        </div>
      </div>
      {speechError && <div className={styles.errorMessage}>{speechError}</div>}
    </form>
  );
};

export default ChatInput;