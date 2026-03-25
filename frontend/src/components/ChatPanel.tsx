import React, { useState } from "react";

type QueryResponse = {
  ok: boolean;
  answer: string;
  template?: string;
  params?: Record<string, unknown>;
  result?: any;
};

type Props = {
  apiBaseUrl: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  detail?: QueryResponse;
};

export default function ChatPanel({ apiBaseUrl }: Props): JSX.Element {
  const [question, setQuestion] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", text: "Hi! I can help you analyze the Order to Cash process." }
  ]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  async function askQuestion(): Promise<void> {
    const userText = question.trim();
    if (!userText) return;
    setLoading(true);
    setError("");
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setQuestion("");
    try {
      const res = await fetch(`${apiBaseUrl}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userText }),
      });
      const data = (await res.json()) as QueryResponse;
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer, detail: data }]);
    } catch (err) {
      setError("Failed to call query endpoint.");
    } finally {
      setLoading(false);
    }
  }

  function handleInputKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void askQuestion();
    }
  }

  return (
    <div style={{ border: "1px solid #d9d9d9", borderRadius: 10, background: "#fff", height: "72vh", display: "flex", flexDirection: "column", boxShadow: "0 10px 30px rgba(15,23,42,0.08)" }}>
      <div style={{ padding: 12, borderBottom: "1px solid #ececec" }}>
        <div style={{ fontSize: 12, color: "#111", fontWeight: 700 }}>Chat with Graph</div>
        <div style={{ fontSize: 10, color: "#777" }}>Order to Cash</div>
      </div>
      <div style={{ padding: "10px 12px", fontSize: 13 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Fryday AI</div>
        <div style={{ color: "#666", fontSize: 12 }}>Graph Agent</div>
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "0 12px 12px" }}>
        {error && <div style={{ color: "crimson", marginBottom: 8 }}>{error}</div>}
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: "#666", marginBottom: 4, textAlign: msg.role === "user" ? "right" : "left" }}>
              {msg.role === "user" ? "You" : "Fryday AI"}
            </div>
            <div
              style={{
                background: msg.role === "user" ? "#151515" : "#fff",
                color: msg.role === "user" ? "#fff" : "#111",
                border: msg.role === "user" ? "1px solid #151515" : "1px solid #ececec",
                padding: "9px 11px",
                borderRadius: 10,
                marginLeft: msg.role === "user" ? 40 : 0,
                marginRight: msg.role === "user" ? 0 : 40
              }}
            >
              {msg.text}
              {msg.role === "assistant" && msg.detail?.template && (
                <div style={{ marginTop: 6, fontSize: 11, color: "#666" }}>
                  Template: {msg.detail.template}
                </div>
              )}
              {msg.role === "assistant" && msg.detail?.result && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: "#444", marginBottom: 4 }}>Result data:</div>
                  <pre
                    style={{
                      background: "#f9fafb",
                      border: "1px solid #e5e7eb",
                      borderRadius: 8,
                      padding: 8,
                      marginTop: 2,
                      fontSize: 10,
                      overflowX: "auto",
                      maxHeight: 180
                    }}
                  >
                    {JSON.stringify(msg.detail.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div style={{ borderTop: "1px solid #ececec", padding: 12 }}>
        <div style={{ fontSize: 11, color: "#666", marginBottom: 6 }}>Analyze anything</div>
        <div style={{ display: "flex", gap: 8 }}>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleInputKeyDown}
            rows={2}
            style={{ width: "100%", resize: "none", border: "1px solid #d1d5db", borderRadius: 8, padding: 8, fontFamily: "inherit" }}
            placeholder="Ask dataset question..."
          />
          <button
            onClick={askQuestion}
            disabled={loading}
            style={{
              minWidth: 70,
              border: "1px solid #111827",
              background: "#111827",
              color: "#fff",
              borderRadius: 8,
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
        <div style={{ marginTop: 6, fontSize: 10, color: "#9ca3af" }}>Press Enter to send, Shift+Enter for newline</div>
      </div>
    </div>
  );
}
