"""Shared pytest fixtures for cosmograph tests."""

import pytest

from cosmograph.models import Edge, Graph, Node


@pytest.fixture
def empty_graph() -> Graph:
    """Fresh Graph instance for each test."""
    return Graph()


@pytest.fixture
def graph_with_nodes() -> Graph:
    """Graph with 3 sample nodes of category 'test'."""
    graph = Graph()
    graph.add_node("node1", "Node One", "test", "First test node")
    graph.add_node("node2", "Node Two", "test", "Second test node")
    graph.add_node("node3", "Node Three", "test", "Third test node")
    return graph


@pytest.fixture
def sample_node() -> Node:
    """Single Node instance for unit tests."""
    return Node(
        id="sample_node",
        label="Sample Node",
        category="test",
        description="A sample node for testing",
        source_file="test.txt",
    )


@pytest.fixture
def sample_edge() -> Edge:
    """Single Edge instance for unit tests."""
    return Edge(
        source="source_node",
        target="target_node",
        edge_type="references",
    )
