"""Tests for HTMLGenerator output."""

import pytest
from pathlib import Path

from cosmograph.generators.html import HTMLGenerator
from cosmograph.models import Graph


class TestHTMLGenerator:
    """Tests for HTMLGenerator output."""

    @pytest.fixture
    def generator(self):
        return HTMLGenerator()

    @pytest.fixture
    def sample_graph(self):
        graph = Graph(title="Test Graph")
        graph.add_node("node1", "Node One", "category")
        graph.add_node("node2", "Node Two", "category")
        graph.add_edge("node1", "node2", "relates")
        return graph

    def test_generates_html_file(self, generator, sample_graph, tmp_path):
        output = tmp_path / "output.html"
        result = generator.generate(sample_graph, output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_html_contains_title(self, generator, sample_graph, tmp_path):
        output = tmp_path / "output.html"
        generator.generate(sample_graph, output)
        html = output.read_text()
        assert "<title>Test Graph</title>" in html

    def test_html_contains_d3(self, generator, sample_graph, tmp_path):
        output = tmp_path / "output.html"
        generator.generate(sample_graph, output)
        html = output.read_text()
        assert "d3.v7.min.js" in html
        assert "d3.forceSimulation" in html

    def test_html_contains_node_data(self, generator, sample_graph, tmp_path):
        output = tmp_path / "output.html"
        generator.generate(sample_graph, output)
        html = output.read_text()
        assert "Node One" in html
        assert "Node Two" in html

    def test_html_self_contained(self, generator, sample_graph, tmp_path):
        """Verify no external script fetches except D3 CDN."""
        output = tmp_path / "output.html"
        generator.generate(sample_graph, output)
        html = output.read_text()
        # Only external script resource should be D3
        # (branding link to GitHub is a regular <a> link, not a fetch)
        assert html.count('src="https://') == 1
        assert "d3js.org" in html
