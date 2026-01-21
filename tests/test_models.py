"""Unit tests for Graph, Node, Edge data models."""

import pytest

from cosmograph.models import Edge, Graph, Node


class TestNode:
    """Tests for Node dataclass."""

    def test_to_dict_truncates_label(self) -> None:
        """Verify label truncated to 60 chars."""
        long_label = "A" * 100
        node = Node(id="test", label=long_label, category="test")
        result = node.to_dict()
        assert len(result["label"]) == 60
        assert result["label"] == "A" * 60

    def test_to_dict_truncates_description(self) -> None:
        """Verify description truncated to 150 chars."""
        long_desc = "B" * 200
        node = Node(id="test", label="Test", category="test", description=long_desc)
        result = node.to_dict()
        assert len(result["description"]) == 150
        assert result["description"] == "B" * 150

    def test_to_dict_structure(self, sample_node: Node) -> None:
        """Verify dict has id, label, category, description keys."""
        result = sample_node.to_dict()
        assert "id" in result
        assert "label" in result
        assert "category" in result
        assert "description" in result
        assert result["id"] == "sample_node"
        assert result["label"] == "Sample Node"
        assert result["category"] == "test"

    def test_to_dict_empty_description(self) -> None:
        """Verify empty description handled correctly."""
        node = Node(id="test", label="Test", category="test", description="")
        result = node.to_dict()
        assert result["description"] == ""


class TestEdge:
    """Tests for Edge dataclass."""

    def test_to_dict_structure(self, sample_edge: Edge) -> None:
        """Verify dict has source, target, type keys."""
        result = sample_edge.to_dict()
        assert "source" in result
        assert "target" in result
        assert "type" in result
        assert result["source"] == "source_node"
        assert result["target"] == "target_node"

    def test_edge_type_in_dict(self, sample_edge: Edge) -> None:
        """Verify edge_type maps to 'type' key."""
        result = sample_edge.to_dict()
        assert result["type"] == "references"
        assert "edge_type" not in result


class TestGraphCleanId:
    """Tests for Graph._clean_id() method."""

    def test_removes_special_characters(self, empty_graph: Graph) -> None:
        """'Test!@#$Node' -> 'TestNode'."""
        result = empty_graph._clean_id("Test!@#$Node")
        assert result == "TestNode"

    def test_collapses_whitespace(self, empty_graph: Graph) -> None:
        """'Test   Node' -> 'Test Node'."""
        result = empty_graph._clean_id("Test   Node")
        assert result == "Test Node"

    def test_truncates_to_100_chars(self, empty_graph: Graph) -> None:
        """150 chars input -> 100 char output."""
        long_input = "A" * 150
        result = empty_graph._clean_id(long_input)
        assert len(result) == 100

    def test_handles_empty_string(self, empty_graph: Graph) -> None:
        """Empty string -> empty string."""
        result = empty_graph._clean_id("")
        assert result == ""

    def test_preserves_hyphens(self, empty_graph: Graph) -> None:
        """Hyphens should be preserved."""
        result = empty_graph._clean_id("test-node-id")
        assert result == "test-node-id"

    def test_strips_leading_trailing_whitespace(self, empty_graph: Graph) -> None:
        """Leading/trailing whitespace stripped."""
        result = empty_graph._clean_id("  Test Node  ")
        assert result == "Test Node"


class TestGraphAddNode:
    """Tests for Graph.add_node() method."""

    def test_adds_new_node(self, empty_graph: Graph) -> None:
        """Returns clean ID, node in graph.nodes."""
        result_id = empty_graph.add_node("test_node", "Test Node", "test")
        assert result_id == "test_node"
        assert result_id in empty_graph.nodes
        assert empty_graph.nodes[result_id].label == "Test Node"

    def test_deduplicates_nodes(self, empty_graph: Graph) -> None:
        """Same ID returns existing, doesn't duplicate."""
        empty_graph.add_node("test_node", "Original", "test")
        empty_graph.add_node("test_node", "Duplicate", "test")
        assert len(empty_graph.nodes) == 1
        # Original should be preserved
        assert empty_graph.nodes["test_node"].label == "Original"

    def test_returns_clean_id(self, empty_graph: Graph) -> None:
        """ID cleaning applied to return value."""
        result_id = empty_graph.add_node("Test!@#Node", "Test", "test")
        assert result_id == "TestNode"
        assert "TestNode" in empty_graph.nodes

    def test_stores_description(self, empty_graph: Graph) -> None:
        """Description is stored in node."""
        empty_graph.add_node("test", "Test", "test", description="A description")
        assert empty_graph.nodes["test"].description == "A description"

    def test_stores_source_file(self, empty_graph: Graph) -> None:
        """Source file is stored in node."""
        empty_graph.add_node("test", "Test", "test", source_file="test.txt")
        assert empty_graph.nodes["test"].source_file == "test.txt"


class TestGraphAddEdge:
    """Tests for Graph.add_edge() method."""

    def test_adds_edge_successfully(self, graph_with_nodes: Graph) -> None:
        """Returns True, edge in graph.edges."""
        result = graph_with_nodes.add_edge("node1", "node2", "references")
        assert result is True
        assert len(graph_with_nodes.edges) == 1
        edge = graph_with_nodes.edges[0]
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.edge_type == "references"

    def test_prevents_self_loops(self, graph_with_nodes: Graph) -> None:
        """Same source/target returns False."""
        result = graph_with_nodes.add_edge("node1", "node1", "references")
        assert result is False
        assert len(graph_with_nodes.edges) == 0

    def test_prevents_duplicate_edges(self, graph_with_nodes: Graph) -> None:
        """Same edge twice returns False second time."""
        first_result = graph_with_nodes.add_edge("node1", "node2", "references")
        second_result = graph_with_nodes.add_edge("node1", "node2", "references")
        assert first_result is True
        assert second_result is False
        assert len(graph_with_nodes.edges) == 1

    def test_allows_different_edge_types(self, graph_with_nodes: Graph) -> None:
        """Same nodes, different type allowed."""
        first_result = graph_with_nodes.add_edge("node1", "node2", "references")
        second_result = graph_with_nodes.add_edge("node1", "node2", "amends")
        assert first_result is True
        assert second_result is True
        assert len(graph_with_nodes.edges) == 2

    def test_cleans_source_and_target_ids(self, graph_with_nodes: Graph) -> None:
        """Source and target IDs are cleaned."""
        graph_with_nodes.add_node("clean_node", "Clean", "test")
        result = graph_with_nodes.add_edge("node1!", "clean_node", "references")
        assert result is True
        edge = graph_with_nodes.edges[0]
        assert edge.source == "node1"


class TestGraphStats:
    """Tests for Graph.get_stats() method."""

    def test_get_stats_counts(self, graph_with_nodes: Graph) -> None:
        """Verify node/edge counts accurate."""
        graph_with_nodes.add_edge("node1", "node2", "references")
        graph_with_nodes.add_edge("node2", "node3", "references")
        stats = graph_with_nodes.get_stats()
        assert stats["nodes"] == 3
        assert stats["edges"] == 2

    def test_get_stats_categories(self, graph_with_nodes: Graph) -> None:
        """Verify category breakdown correct."""
        stats = graph_with_nodes.get_stats()
        assert "categories" in stats
        assert stats["categories"]["test"] == 3

    def test_get_stats_multiple_categories(self, empty_graph: Graph) -> None:
        """Verify multiple categories counted correctly."""
        empty_graph.add_node("n1", "Node 1", "category_a")
        empty_graph.add_node("n2", "Node 2", "category_a")
        empty_graph.add_node("n3", "Node 3", "category_b")
        stats = empty_graph.get_stats()
        assert stats["categories"]["category_a"] == 2
        assert stats["categories"]["category_b"] == 1

    def test_get_stats_empty_graph(self, empty_graph: Graph) -> None:
        """Verify stats for empty graph."""
        stats = empty_graph.get_stats()
        assert stats["nodes"] == 0
        assert stats["edges"] == 0
        assert stats["categories"] == {}


class TestGraphToJson:
    """Tests for Graph.to_json() method."""

    def test_to_json_structure(self, graph_with_nodes: Graph) -> None:
        """Verify JSON output structure."""
        graph_with_nodes.add_edge("node1", "node2", "references")
        result = graph_with_nodes.to_json()
        assert "nodes" in result
        assert "edges" in result
        assert "title" in result
        assert "stats" in result

    def test_to_json_nodes_list(self, graph_with_nodes: Graph) -> None:
        """Verify nodes are converted to list of dicts."""
        result = graph_with_nodes.to_json()
        assert isinstance(result["nodes"], list)
        assert len(result["nodes"]) == 3
        # Each node should have to_dict() structure
        node = result["nodes"][0]
        assert "id" in node
        assert "label" in node
        assert "category" in node

    def test_to_json_edges_list(self, graph_with_nodes: Graph) -> None:
        """Verify edges are converted to list of dicts."""
        graph_with_nodes.add_edge("node1", "node2", "references")
        result = graph_with_nodes.to_json()
        assert isinstance(result["edges"], list)
        assert len(result["edges"]) == 1
        edge = result["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
