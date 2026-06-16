import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages }) {
  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <h2>Welcome to OncoGuide</h2>
          <p>Ask a cancer education, screening, report, or clinical-trial question.</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <MessageBubble key={index} role={message.role} text={message.text} />
        ))
      )}
    </div>
  );
}