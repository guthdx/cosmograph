// frontend/src/components/DownloadButtons.tsx
import { getDownloadHtmlUrl, getDownloadCsvUrl } from '../services/api';
import './DownloadButtons.css';

interface DownloadButtonsProps {
  jobId: string;
}

export function DownloadButtons({ jobId }: DownloadButtonsProps) {
  const htmlUrl = getDownloadHtmlUrl(jobId);
  const csvUrl = getDownloadCsvUrl(jobId);

  return (
    <div className="download-buttons">
      <a href={htmlUrl} download className="btn-download btn-html">
        Download HTML
      </a>
      <a href={csvUrl} download className="btn-download btn-csv">
        Download CSV
      </a>
    </div>
  );
}
