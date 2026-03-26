import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { ForceGraphMethods } from "react-force-graph-2d";

type GraphNode = {
  id: string;
  type: string;
  metadata: Record<string, unknown>;
};

type GraphEdge = {
  source: string;
  target: string;
  label: string;
};

type GraphOverview = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: { node_count: number; edge_count: number };
};

type ExpandResponse = {
  node: GraphNode | null;
  neighbors: GraphNode[];
  edges: GraphEdge[];
};

type Props = {
  apiBaseUrl: string;
};

function formatNodeType(nodeType: string): string {
  if (nodeType === "sales_order") return "Sales Order";
  if (nodeType === "delivery_document") return "Delivery";
  if (nodeType === "billing_document") return "Billing";
  if (nodeType === "journal_entry") return "Journal Entry";
  if (nodeType === "payment") return "Payment";
  if (nodeType === "customer") return "Customer";
  if (nodeType === "product") return "Product";
  if (nodeType === "address") return "Address";
  return nodeType;
}

export default function GraphViewer({ apiBaseUrl }: Props): JSX.Element {
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [overview, setOverview] = useState<GraphOverview | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expanded, setExpanded] = useState<ExpandResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [hideOverlay, setHideOverlay] = useState<boolean>(false);
  const [graphSize, setGraphSize] = useState<{ width: number; height: number }>({ width: 900, height: 640 });

  async function loadOverview(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiBaseUrl}/api/graph/overview`);
      const data = (await res.json()) as GraphOverview;
      setOverview(data);
    } catch (err) {
      setError("Failed to load graph overview.");
    } finally {
      setLoading(false);
    }
  }

  async function expandNode(nodeId: string): Promise<void> {
    if (!nodeId) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiBaseUrl}/api/graph/expand/${encodeURIComponent(nodeId)}`);
      const data = (await res.json()) as ExpandResponse;
      setExpanded(data);
    } catch (err) {
      setError("Failed to expand selected node.");
    } finally {
      setLoading(false);
    }
  }

  const graphData = useMemo(() => {
    if (!overview) {
      return { nodes: [], links: [] as Array<{ source: string; target: string; label: string }> };
    }
    return {
      nodes: overview.nodes.map((node) => ({ ...node })),
      links: overview.edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        label: edge.label,
      })),
    };
  }, [overview]);

  const connectionCount = useMemo(() => {
    if (!overview || !selectedNode) return 0;
    return overview.edges.filter((edge) => edge.source === selectedNode.id || edge.target === selectedNode.id).length;
  }, [overview, selectedNode]);

  useEffect(() => {
    void loadOverview();
  }, []);

  // ✅ FIX 1: Delay zoomToFit (core issue)
  useEffect(() => {
    if (!overview || !graphRef.current) return;

    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(500, 40);
    }, 400);

    return () => clearTimeout(timer);
  }, [overview]);

  // ✅ FIX 2: Sync width AND height with container
  useEffect(() => {
    const refreshSize = (): void => {
      const width = containerRef.current?.clientWidth ?? 900;
      const height = containerRef.current?.clientHeight ?? 640;

      setGraphSize({
        width: Math.max(480, width - 2),
        height: Math.max(400, height - 2),
      });
    };

    refreshSize();
    window.addEventListener("resize", refreshSize);
    return () => window.removeEventListener("resize", refreshSize);
  }, []);

  // ✅ FIX 3: Re-fit graph on resize
  useEffect(() => {
    const handleResize = () => {
      graphRef.current?.zoomToFit(500, 40);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div ref={containerRef} style={{ position: "relative", border: "1px solid #d9d9d9", borderRadius: 6, background: "#fff", height: "72vh", overflow: "hidden" }}>
      <div style={{ display: "flex", gap: 8, padding: 10, position: "absolute", zIndex: 5 }}>
        <button
          onClick={() => graphRef.current?.zoomToFit(500, 40)}
          style={{ border: "1px solid #bbb", borderRadius: 4, background: "#f7f7f7", padding: "4px 8px" }}
        >
          Minimize
        </button>
        <button
          onClick={() => setHideOverlay((value) => !value)}
          style={{ border: "1px solid #111", borderRadius: 4, color: "#fff", background: "#111", padding: "4px 8px" }}
        >
          {hideOverlay ? "Show Granular Overlay" : "Hide Granular Overlay"}
        </button>
      </div>

      {!hideOverlay && overview && (
        <div
          style={{
            position: "absolute",
            zIndex: 4,
            marginTop: 52,
            marginLeft: 10,
            background: "rgba(255,255,255,0.9)",
            border: "1px solid #ddd",
            borderRadius: 6,
            padding: 8,
            fontSize: 12,
            maxWidth: 360,
            boxShadow: "0 6px 18px rgba(15, 23, 42, 0.08)"
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 999, background: "#e0f2fe", color: "#075985" }}>Sales</span>
            <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 999, background: "#dbeafe", color: "#1d4ed8" }}>Delivery</span>
            <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 999, background: "#ede9fe", color: "#6d28d9" }}>Billing</span>
          </div>
          <strong>Graph:</strong> {overview.summary.node_count} nodes, {overview.summary.edge_count} edges
          {expanded?.node && (
            <div style={{ marginTop: 6 }}>
              <strong>Selected:</strong> {expanded.node.id}
            </div>
          )}
          {expanded && (
            <div style={{ marginTop: 4 }}>
              <strong>Neighbors:</strong> {expanded.neighbors.map((n) => n.id).join(", ") || "None"}
            </div>
          )}
        </div>
      )}

      {!hideOverlay && selectedNode && (
        <div
          style={{
            position: "absolute",
            zIndex: 6,
            left: 280,
            top: 60,
            width: 240,
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
            padding: 10,
            fontSize: 12,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{selectedNode.id}</div>
            <button
              onClick={() => setSelectedNode(null)}
              style={{ border: "none", background: "transparent", color: "#6b7280", cursor: "pointer", fontSize: 14 }}
            >
              x
            </button>
          </div>
          <div style={{ marginBottom: 6 }}>
            <strong>Entity:</strong> {formatNodeType(selectedNode.type)}
          </div>
          {Object.entries(selectedNode.metadata ?? {})
            .filter(([_, value]) => value !== "" && value !== null && value !== undefined)
            .slice(0, 8)
            .map(([key, value]) => (
              <div key={key} style={{ marginBottom: 2 }}>
                <strong>{key}:</strong> {String(value)}
              </div>
            ))}
          <div style={{ marginTop: 8 }}>
            <strong>Connections:</strong> {connectionCount}
          </div>
        </div>
      )}

      {error && <div style={{ color: "crimson", padding: "72px 12px 0" }}>{error}</div>}

      <ForceGraph2D
        ref={graphRef}
        width={graphSize.width}
        height={graphSize.height}
        graphData={graphData}
        nodeLabel={(node) => `${(node as GraphNode).id} (${(node as GraphNode).type})`}
        nodeRelSize={3}
        linkWidth={0.7}
        linkColor={() => "rgba(126, 180, 255, 0.45)"}
        backgroundColor="#ffffff"
        nodeCanvasObject={(node, ctx, globalScale) => {
          const item = node as GraphNode;
          const label = item.id;
          const fontSize = 8 / globalScale;
          ctx.font = `${fontSize}px Arial`;

          if (item.type === "billing_document") ctx.fillStyle = "#8b5cf6";
          else if (item.type === "delivery_document") ctx.fillStyle = "#60a5fa";
          else if (item.type === "sales_order") ctx.fillStyle = "#fb7185";
          else if (item.type === "journal_entry") ctx.fillStyle = "#22c55e";
          else if (item.type === "payment") ctx.fillStyle = "#f59e0b";
          else if (item.type === "customer") ctx.fillStyle = "#14b8a6";
          else if (item.type === "address") ctx.fillStyle = "#64748b";
          else if (item.type === "product") ctx.fillStyle = "#ec4899";
          else ctx.fillStyle = "#64748b";

          ctx.beginPath();
          ctx.arc(node.x || 0, node.y || 0, 2.5, 0, 2 * Math.PI, false);
          ctx.fill();

          if (globalScale > 2.2) {
            ctx.fillStyle = "#333";
            ctx.fillText(label, (node.x || 0) + 3, (node.y || 0) + 3);
          }
        }}
        onNodeClick={(node) => {
          const item = node as GraphNode;
          setSelectedNode(item);
          void expandNode(item.id);
        }}
      />

      {loading && (
        <div style={{ position: "absolute", bottom: 12, left: 12, background: "#fff", border: "1px solid #ddd", borderRadius: 4, padding: "4px 8px", fontSize: 12 }}>
          Loading...
        </div>
      )}
      {selectedNode && (
        <div style={{ position: "absolute", bottom: 12, right: 12, background: "#fff", border: "1px solid #ddd", borderRadius: 4, padding: "4px 8px", fontSize: 12 }}>
          Selected: {selectedNode.id}
        </div>
      )}
    </div>
  );
}