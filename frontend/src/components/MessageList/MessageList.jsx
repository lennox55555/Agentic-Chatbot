import { Fragment } from "react"
import MessageItem from "../MessageItem/MessageItem"
import styles from "./MessageList.module.css"
import 'bootstrap-icons/font/bootstrap-icons.css';

const MessageList = ({ messages, isLoading }) => {
  return (
    <div className={styles.messageList}>
      {messages.length === 0 ? (
        <div className={styles.emptyChat}>
          <p><b>Developers' Note:</b> BlueAgent should only be used for informational purposes and
          is not meant to represent Duke University's views or opinions. This chatbot is not used for business purposes. It is only meant to make
          information about Duke University more accessible to the general public, incoming students, or students considering applying to Duke University.</p>
          <p>Please click on the info button or <a href="./evaluation_results/evaluation_report.html" target="_noblank"><nobr>here</nobr></a> to learn more about the models' performances. </p>
        </div>
      ) : (
        <Fragment>
          {messages.map((message) => (
            <MessageItem key={message.id} message={message} />
          ))}
        </Fragment>
      )}

      {isLoading && (
        <div className={`d-flex justify-content-start mb-4 ${styles.loadingContainer}`}>
          <div className={styles.avatar}>
            <span>BlueAgent is looking for an answer...</span>
          </div>
          <div className={`${styles.messageBubble} ${styles.aiMessage}`}>
            <div className={styles.typingIndicator}>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MessageList

