// frontend/src/components/GraphPreview.tsx
import './GraphPreview.css';

interface GraphPreviewProps {
  jobId: string;
}

/**
 * Display the generated graph visualization in an iframe.
 *
 * Uses the self-contained HTML from the download endpoint.
 * The HTML includes embedded D3.js and all data - no additional loading needed.
 */
export function GraphPreview({ jobId }: GraphPreviewProps) {
  const htmlUrl = `/api/download/${jobId}`;

  return (
    <div className="graph-preview">
      <iframe
        src={htmlUrl}
        title="Knowledge Graph Visualization"
        sandbox="allow-scripts"
      />
    </div>
  );
}
