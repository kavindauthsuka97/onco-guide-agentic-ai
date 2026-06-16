import { useState } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import ProgressPanel from "./components/ProgressPanel";
import ReviewDashboard from "./components/ReviewDashboard";

import { streamMessage } from "./services/api";

import "./App.css";

const NODE_DISPLAY_NAMES = {
  unified_input_guardrail: "Safety check",
  supervisor: "Care pathway selection",
  screening_agent: "Symptom screening",
  rag_agent: "Medical knowledge search",
  clinical_trial_agent: "Clinical trial search",
  report_explanation_agent: "Report review",
  react_agent: "Multi-step medical search",
  manual_tool_agent: "Medical tool lookup",
  general_chat_agent: "General medical guidance",
  reflection_agent: "Answer quality review",
  claim_verification_agent: "Evidence verification",
  human_review: "Clinician review queue",
  output_guardrail: "Final safety check",
};

function getReadableStep(data) {
  if (data?.node && NODE_DISPLAY_NAMES[data.node]) {
    return NODE_DISPLAY_NAMES[data.node];
  }

  if (data?.node) {
    return data.node.replaceAll("_", " ");
  }

  return data?.message || "Processing";
}

export default function App() {
  const [activePage, setActivePage] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);

  function handleNewChat() {
    setMessages([]);
    setConversationId(null);
    setSteps([]);
    setLoading(false);
    setActivePage("chat");
  }

  async function handleSend(message) {
    const userMessage = {
      role: "user",
      text: message,
    };

    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setSteps([]);
    setLoading(true);

    try {
      await streamMessage({
        message: message,
        conversationId: conversationId,

        onStart: (data) => {
          setConversationId(data.conversation_id);
          setSteps(["Request received"]);
        },

        onProgress: (data) => {
          const readableStep = getReadableStep(data);
          setSteps((previous) => [...previous, readableStep]);
        },

        onFinal: (data) => {
          setConversationId(data.conversation_id);

          const assistantMessage = {
            role: "assistant",
            text: data.answer,
          };

          setMessages([...updatedMessages, assistantMessage]);
          setSteps((previous) => [...previous, "Response ready"]);
          setLoading(false);
        },

        onError: (data) => {
          const errorMessage = {
            role: "assistant",
            text: `Error: ${data.message || "Streaming failed"}`,
          };

          setMessages([...updatedMessages, errorMessage]);
          setSteps((previous) => [...previous, "Unable to complete request"]);
          setLoading(false);
        },
      });
    } catch (error) {
      const errorMessage = {
        role: "assistant",
        text: `Error: ${error.message}`,
      };

      setMessages([...updatedMessages, errorMessage]);
      setSteps((previous) => [...previous, "Connection stopped"]);
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>OncoGuide Agentic AI</h1>
          <p>
            Educational cancer assistant with RAG, agents, guardrails, MCP, and
            human review.
          </p>

          {conversationId && (
            <p className="conversation-id">
              Current session: {conversationId.slice(0, 8)}...
            </p>
          )}
        </div>

        <nav className="top-nav">
          <button
            className={activePage === "chat" ? "nav-button active" : "nav-button"}
            onClick={() => setActivePage("chat")}
          >
            Chat
          </button>

          <button className="nav-button new-chat-button" onClick={handleNewChat}>
            New Chat
          </button>

          <button
            className={activePage === "review" ? "nav-button active" : "nav-button"}
            onClick={() => setActivePage("review")}
          >
            Human Review
          </button>
        </nav>
      </header>

      {activePage === "chat" ? (
        <div className="main-layout">
          <main className="chat-card">
            <ChatWindow messages={messages} />
            <ChatInput onSend={handleSend} loading={loading} />
          </main>

          <aside>
            <ProgressPanel steps={steps} />
          </aside>
        </div>
      ) : (
        <ReviewDashboard />
      )}
    </div>
  );
}