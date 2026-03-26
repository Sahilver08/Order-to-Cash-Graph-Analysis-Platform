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
  const graphRef = useRef<ForceGraphMethods>();
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [overview, setOverview] = useState<GraphOverview | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expanded, setExpanded] = useState<ExpandResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [hideOverlay, setHideOverlay] = useState<boolean>(false);

  const [graphSize, setGraphSize] = useState({
    width: 900,
    height: 640,
  });

  async function loadOverview() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiBaseUrl}/api/graph/overview`);
      const data = await res.json();
      setOverview(data);
    } catch {
      setError("Failed to load graph overview.");
    } finally {
      setLoading(false);
    }
  }

  async function expandNode(nodeId: string) {
    if (!nodeId) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(
        `${apiBaseUrl}/api/graph/expand/${encodeURIComponent(nodeId)}`
      );
      const data = await res.json();
      setExpanded(data);
    } catch {
      setError("Failed to expand selected node.");
    } finally {
      setLoading(false);
    }
  }

  const graphData = useMemo(() => {
    if (!overview) return { nodes: [], links: [] };
    return {
      nodes: overview.nodes.map((n) => ({ ...n })),
      links: overview.edges.map((e) => ({
        source: e.source,
        target: e.target,
        label: e.label,
      })),
    };
  }, [overview]);

  useEffect(() => {
    loadOverview();
  }, []);

  // Delay zoom for proper render
  useEffect(() => {
    if (!overview || !graphRef.current) return;

    const timer = setTimeout(() => {
      graphRef.current?.zoomToFit(500, 40);
    }, 400);

    return () => clearTimeout(timer);
  }, [overview]);

  // Proper width + height sync
  useEffect(() => {
    const updateSize = () => {
      const width = containerRef.current?.clientWidth || 900;
      const height = containerRef.current?.clientHeight || 640;

      setGraphSize({
        width: Math.max(480, width),
        height: Math.max(400, height),
      });
    };

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  // Re-fit on resize
  useEffect(() => {
    const handleResize = () => {
      graphRef.current?.zoomToFit(500, 40);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        border: "1px solid #d9d9d9",
        borderRadius: 6,
        background: "#fff",
        height: "72vh",
        minHeight: "600px",
        overflow: "hidden",
      }}
    >
      <ForceGraph2D
        ref={graphRef}
        width={graphSize.width}
        height={graphSize.height}
        graphData={graphData}
        nodeLabel={(node: any) => `${node.id} (${node.type})`}
        nodeRelSize={3}
        linkWidth={0.7}
        linkColor={() => "rgba(126, 180, 255, 0.45)"}
        backgroundColor="#ffffff"
        onNodeClick={(node: any) => {
          setSelectedNode(node);
          expandNode(node.id);
        }}
      />

      {loading && (
        <div style={{ position: "absolute", bottom: 12, left: 12 }}>
          Loading...
        </div>
      )}
    </div>
  );
}