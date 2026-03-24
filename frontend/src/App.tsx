import React from "react";

import ChatPanel from "./components/ChatPanel";
import GraphViewer from "./components/GraphViewer";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App(): JSX.Element {
  return (
    <div
      style={{
        padding: 12,
        fontFamily: "Inter, Segoe UI, Arial, sans-serif",
        background: "linear-gradient(180deg, #f8fafc 0%, #f2f5f9 100%)",
        minHeight: "100vh"
      }}
    >
      <div style={{ fontSize: 12, marginBottom: 10, color: "#6b7280", letterSpacing: 0.2 }}>
        Mapping / <strong style={{ color: "#111827" }}>Order to Cash</strong>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(680px, 1fr) 320px", gap: 14, alignItems: "start" }}>
        <GraphViewer apiBaseUrl={API_BASE_URL} />
        <ChatPanel apiBaseUrl={API_BASE_URL} />
      </div>
    </div>
  );
}
