export default function MessageBubble({ role, text }) {
    const isUser = role === "user";
  
    return (
      <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
        <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
          {text}
        </div>
      </div>
    );
  }