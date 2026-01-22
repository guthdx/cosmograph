// frontend/src/components/ProgressDisplay.tsx
import './ProgressDisplay.css';

interface ProgressDisplayProps {
  status: string;
  progress: number;
  total: number;
}

export function ProgressDisplay({ status, progress, total }: ProgressDisplayProps) {
  const percent = total > 0 ? Math.round((progress / total) * 100) : 0;

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return 'Preparing...';
      case 'processing':
        return `Processing file ${progress} of ${total}`;
      case 'completed':
        return 'Extraction complete!';
      case 'failed':
        return 'Extraction failed';
      default:
        return status;
    }
  };

  return (
    <div className="progress-display">
      <div className="progress-header">
        <span className="progress-status">{getStatusText()}</span>
        <span className="progress-percent">{percent}%</span>
      </div>
      <div className="progress-bar">
        <div
          className={`progress-fill ${status === 'completed' ? 'complete' : ''} ${status === 'failed' ? 'failed' : ''}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
