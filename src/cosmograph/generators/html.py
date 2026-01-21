"""HTML visualization generator."""

import json
from pathlib import Path

from ..models import Graph


class HTMLGenerator:
    """Generate interactive HTML visualization from a knowledge graph."""

    # Category colors for visualization
    CATEGORY_COLORS = {
        "document": "#e91e63",
        "article": "#9c27b0",
        "title": "#673ab7",
        "chapter": "#3f51b5",
        "section": "#2196f3",
        "ordinance": "#00bcd4",
        "authority": "#ff9800",
        "right": "#4caf50",
        "offense": "#f44336",
        "penalty": "#ff5722",
        "procedure": "#795548",
        "definition": "#607d8b",
        "place": "#8bc34a",
        "entity": "#ffc107",
        "concept": "#9e9e9e",
        "constitution": "#e91e63",
        "code": "#9c27b0",
        "proper_noun": "#4caf50",
        "acronym": "#ff9800",
        "quoted_term": "#2196f3",
        "section_ref": "#673ab7",
    }

    def generate(self, graph: Graph, output_path: Path, title: str = None) -> Path:
        """Generate an interactive HTML visualization."""
        title = title or graph.title

        nodes_json = json.dumps([n.to_dict() for n in graph.nodes.values()])
        edges_json = json.dumps([e.to_dict() for e in graph.edges])
        colors_json = json.dumps(self.CATEGORY_COLORS)
        stats = graph.get_stats()

        html = self._generate_html(title, nodes_json, edges_json, colors_json, stats)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _generate_html(
        self, title: str, nodes_json: str, edges_json: str, colors_json: str, stats: dict
    ) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e0e0e0;
            overflow: hidden;
        }}
        #container {{ display: flex; height: 100vh; width: 100vw; }}
        #sidebar {{
            width: 320px;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        #graph-container {{ flex: 1; position: relative; }}
        svg {{ width: 100%; height: 100%; }}
        h1 {{ font-size: 1.4em; margin-bottom: 5px; color: #fff; }}
        .subtitle {{ font-size: 0.85em; color: #888; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
        .stat-box {{ background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 1.5em; font-weight: bold; color: #4fc3f7; }}
        .stat-label {{ font-size: 0.75em; color: #888; text-transform: uppercase; }}
        .section-title {{ font-size: 0.9em; font-weight: 600; margin: 15px 0 10px; color: #aaa; text-transform: uppercase; }}
        .legend {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 0.8em; cursor: pointer; padding: 4px 8px; border-radius: 4px; background: rgba(255, 255, 255, 0.05); }}
        .legend-item:hover {{ background: rgba(255, 255, 255, 0.1); }}
        .legend-item.inactive {{ opacity: 0.3; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 50%; }}
        #search {{ width: 100%; padding: 10px 12px; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; background: rgba(255, 255, 255, 0.05); color: #fff; font-size: 0.9em; margin-bottom: 15px; }}
        #search::placeholder {{ color: #666; }}
        #search:focus {{ outline: none; border-color: #4fc3f7; }}
        #node-info {{ background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 15px; display: none; }}
        #node-info.visible {{ display: block; }}
        #node-info h3 {{ font-size: 1em; margin-bottom: 8px; color: #fff; word-wrap: break-word; }}
        #node-info .category {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; margin-bottom: 10px; }}
        #node-info .description {{ font-size: 0.85em; color: #aaa; line-height: 1.5; }}
        .controls {{ position: absolute; bottom: 20px; right: 20px; display: flex; gap: 10px; }}
        .control-btn {{ width: 40px; height: 40px; border-radius: 50%; border: none; background: rgba(255, 255, 255, 0.1); color: #fff; font-size: 1.2em; cursor: pointer; }}
        .control-btn:hover {{ background: rgba(255, 255, 255, 0.2); }}
        .tooltip {{ position: absolute; background: rgba(0, 0, 0, 0.9); padding: 8px 12px; border-radius: 6px; font-size: 0.85em; pointer-events: none; opacity: 0; max-width: 250px; z-index: 1000; }}
        .tooltip.visible {{ opacity: 1; }}
        .node {{ cursor: pointer; }}
        .node.dimmed {{ opacity: 0.15; }}
        .link {{ stroke-opacity: 0.4; }}
        .link.dimmed {{ stroke-opacity: 0.05; }}
        .link.highlighted {{ stroke-opacity: 0.8; }}
        .branding {{ position: absolute; bottom: 10px; left: 10px; font-size: 0.7em; color: #555; }}
        .branding a {{ color: #4fc3f7; text-decoration: none; }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h1>{title}</h1>
            <p class="subtitle">Interactive Knowledge Graph</p>
            <div class="stats">
                <div class="stat-box"><div class="stat-value">{stats["nodes"]}</div><div class="stat-label">Nodes</div></div>
                <div class="stat-box"><div class="stat-value">{stats["edges"]}</div><div class="stat-label">Connections</div></div>
            </div>
            <input type="text" id="search" placeholder="Search nodes...">
            <div class="section-title">Categories</div>
            <div class="legend" id="legend"></div>
            <div class="section-title">Selected Node</div>
            <div id="node-info">
                <h3 id="info-title"></h3>
                <span class="category" id="info-category"></span>
                <p class="description" id="info-description"></p>
            </div>
        </div>
        <div id="graph-container">
            <svg id="graph"></svg>
            <div class="controls">
                <button class="control-btn" id="zoom-in">+</button>
                <button class="control-btn" id="zoom-out">−</button>
                <button class="control-btn" id="reset">⟲</button>
            </div>
            <div class="branding">Generated with <a href="https://github.com/guthdx/cosmograph">Cosmograph</a></div>
        </div>
    </div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const nodes = {nodes_json};
        const links = {edges_json};
        const categoryColors = {colors_json};

        let activeCategories = new Set(Object.keys(categoryColors));

        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const svg = d3.select('#graph').attr('viewBox', [0, 0, width, height]);
        const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (e) => g.attr('transform', e.transform));
        svg.call(zoom);
        const g = svg.append('g');

        const nodeIds = new Set(nodes.map(n => n.id));
        const validLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(validLinks).id(d => d.id).distance(60))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(15));

        const link = g.append('g').selectAll('line').data(validLinks).join('line')
            .attr('class', 'link').attr('stroke', '#666').attr('stroke-width', 1);

        const node = g.append('g').selectAll('g').data(nodes).join('g').attr('class', 'node')
            .call(d3.drag()
                .on('start', (e) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; }})
                .on('drag', (e) => {{ e.subject.fx = e.x; e.subject.fy = e.y; }})
                .on('end', (e) => {{ if (!e.active) simulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }}));

        node.append('circle')
            .attr('r', d => Math.min(Math.max(5, validLinks.filter(l => l.source.id === d.id || l.target.id === d.id || l.source === d.id || l.target === d.id).length * 1.2), 20))
            .attr('fill', d => categoryColors[d.category] || '#999')
            .attr('stroke', '#fff').attr('stroke-width', 1);

        const tooltip = document.getElementById('tooltip');
        node.on('mouseover', (e, d) => {{
            tooltip.innerHTML = '<strong>' + d.label + '</strong><br><em>' + d.category + '</em>';
            tooltip.style.left = (e.pageX + 10) + 'px';
            tooltip.style.top = (e.pageY - 10) + 'px';
            tooltip.classList.add('visible');
            const connected = new Set([d.id]);
            validLinks.forEach(l => {{
                if ((l.source.id || l.source) === d.id) connected.add(l.target.id || l.target);
                if ((l.target.id || l.target) === d.id) connected.add(l.source.id || l.source);
            }});
            node.classed('dimmed', n => !connected.has(n.id));
            link.classed('dimmed', l => (l.source.id || l.source) !== d.id && (l.target.id || l.target) !== d.id);
        }}).on('mouseout', () => {{
            tooltip.classList.remove('visible');
            node.classed('dimmed', false);
            link.classed('dimmed', false);
        }}).on('click', (e, d) => {{
            document.getElementById('info-title').textContent = d.label;
            const cat = document.getElementById('info-category');
            cat.textContent = d.category;
            cat.style.background = categoryColors[d.category] || '#999';
            document.getElementById('info-description').textContent = d.description || 'No description';
            document.getElementById('node-info').classList.add('visible');
        }});

        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
            node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        }});

        const legend = document.getElementById('legend');
        [...new Set(nodes.map(n => n.category))].sort().forEach(cat => {{
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.dataset.category = cat;
            item.innerHTML = '<span class="legend-color" style="background:' + (categoryColors[cat] || '#999') + '"></span><span>' + cat + '</span>';
            item.onclick = () => {{
                if (activeCategories.has(cat)) {{ activeCategories.delete(cat); item.classList.add('inactive'); }}
                else {{ activeCategories.add(cat); item.classList.remove('inactive'); }}
                node.style('display', d => activeCategories.has(d.category) ? null : 'none');
                link.style('display', l => {{
                    const sn = nodes.find(n => n.id === (l.source.id || l.source));
                    const tn = nodes.find(n => n.id === (l.target.id || l.target));
                    return sn && tn && activeCategories.has(sn.category) && activeCategories.has(tn.category) ? null : 'none';
                }});
            }};
            legend.appendChild(item);
        }});

        document.getElementById('search').addEventListener('input', (e) => {{
            const q = e.target.value.toLowerCase();
            if (!q) {{ node.style('opacity', 1); link.style('opacity', 1); return; }}
            const matched = new Set(nodes.filter(n => n.label.toLowerCase().includes(q) || (n.description && n.description.toLowerCase().includes(q))).map(n => n.id));
            node.style('opacity', d => matched.has(d.id) ? 1 : 0.1);
            link.style('opacity', l => matched.has(l.source.id || l.source) || matched.has(l.target.id || l.target) ? 1 : 0.1);
        }});

        document.getElementById('zoom-in').onclick = () => svg.transition().call(zoom.scaleBy, 1.3);
        document.getElementById('zoom-out').onclick = () => svg.transition().call(zoom.scaleBy, 0.7);
        document.getElementById('reset').onclick = () => svg.transition().call(zoom.transform, d3.zoomIdentity);
    </script>
</body>
</html>'''
