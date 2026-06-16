import { useState } from "react";

export default function ChatInput({ onSend, loading }) {
  const [message, setMessage] = useState("");

  function handleSend() {
    if (!message.trim() || loading) {
      return;
    }

    onSend(message.trim());
    setMessage("");
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      handleSend();
    }
  }

  return (
    <div className="chat-input-row">
      <input
        className="chat-input"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask OncoGuide..."
        disabled={loading}
      />

      <button className="send-button" onClick={handleSend} disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>
    </div>
  );
}