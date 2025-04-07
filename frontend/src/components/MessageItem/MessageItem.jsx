import React from 'react';
import styles from './MessageItem.module.css'; // Assuming you're using CSS modules

const MessageItem = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`${styles.messageContainer} ${isUser ? styles.userMessage : styles.assistantMessage}`}>
      <div className={styles.avatar}>
        {isUser ? (
          <i className="bi bi-person-circle"></i>
        ) : (
          <div className={styles.botAvatar}>
            <i className="bi bi-robot"></i>
          </div>
        )}
      </div>
      <div className={styles.messageContent}>
        <div className={styles.role}>{isUser ? "You" : "MediSeek"}</div>
        <div className={styles.text}>{message.content}</div>
      </div>
    </div>
  );
};

export default MessageItem;