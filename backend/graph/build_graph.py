from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GraphData:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, str]] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))


class GraphBuilder:
    """
    Minimal graph builder:
    - Reads a dataset CSV
    - Creates one node per row
    - Creates edges based on configured relation column pairs
    """

    def __init__(
        self,
        dataset_path: str,
        node_id_column: str,
        entity_type: str = "record",
        relation_pairs: list[tuple[str, str]] | None = None,
    ) -> None:
        self.dataset_path = Path(dataset_path)
        self.node_id_column = node_id_column
        self.entity_type = entity_type
        self.relation_pairs = relation_pairs or []

    def build(self) -> GraphData:
        rows = self._read_csv_rows()
        graph = GraphData()

        for row in rows:
            node_id = str(row.get(self.node_id_column, "")).strip()
            if not node_id:
                continue

            graph.nodes[node_id] = {
                "id": node_id,
                "type": self.entity_type,
                "metadata": row,
            }

        self._add_relation_edges(graph, rows)
        return graph

    def _read_csv_rows(self) -> list[dict[str, str]]:
        if not self.dataset_path.exists():
            return []

        with self.dataset_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            return [dict(row) for row in reader]

    def _add_relation_edges(self, graph: GraphData, rows: list[dict[str, str]]) -> None:
        # Build a quick reverse index from possible id values to node ids.
        id_index: dict[str, str] = {}
        for node_id in graph.nodes:
            id_index[node_id] = node_id

        for row in rows:
            source = str(row.get(self.node_id_column, "")).strip()
            if not source or source not in graph.nodes:
                continue

            for left_col, right_col in self.relation_pairs:
                left_val = str(row.get(left_col, "")).strip()
                right_val = str(row.get(right_col, "")).strip()

                if not left_val or not right_val:
                    continue

                if left_val != source:
                    continue

                target = id_index.get(right_val)
                if not target:
                    continue

                graph.edges.append(
                    {
                        "source": source,
                        "target": target,
                        "label": f"{left_col}->{right_col}",
                    }
                )
                graph.adjacency[source].append(target)


def get_neighbors(graph: GraphData, node_id: str) -> list[dict[str, Any]]:
    neighbor_ids = graph.adjacency.get(node_id, [])
    return [graph.nodes[n_id] for n_id in neighbor_ids if n_id in graph.nodes]
