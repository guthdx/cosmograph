// frontend/src/App.tsx
import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ExtractionOptions } from './components/ExtractionOptions';
import { ProgressDisplay } from './components/ProgressDisplay';
import { GraphPreview } from './components/GraphPreview';
import { DownloadButtons } from './components/DownloadButtons';
import { useExtraction } from './hooks/useExtraction';
import type { ExtractionOptions as Options } from './types';
import './App.css';

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<Options>({
    extractor: 'auto',
    title: 'Knowledge Graph',
    llmConfirmed: false,
  });

  const extraction = useExtraction();

  const isProcessing = extraction.state === 'uploading' || extraction.state === 'processing';
  const isComplete = extraction.state === 'completed';
  const isFailed = extraction.state === 'failed';
  const canStartExtraction = files.length > 0 && !isProcessing;

  const handleStartExtraction = async () => {
    await extraction.startExtraction(files, options);
  };

  const handleNewExtraction = () => {
    setFiles([]);
    setOptions({
      extractor: 'auto',
      title: 'Knowledge Graph',
      llmConfirmed: false,
    });
    extraction.reset();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Cosmograph</h1>
        <p>Document-to-Knowledge-Graph Service</p>
      </header>

      <main className="app-main">
        {/* Show upload UI when idle or failed */}
        {(extraction.state === 'idle' || isFailed) && (
          <>
            <section className="upload-section">
              <h2>1. Select Files</h2>
              <FileUpload
                onFilesSelected={setFiles}
                selectedFiles={files}
                disabled={isProcessing}
              />
            </section>

            <section className="options-section">
              <h2>2. Configure Extraction</h2>
              <ExtractionOptions
                options={options}
                onChange={setOptions}
                disabled={isProcessing}
              />
            </section>

            {isFailed && extraction.error && (
              <section className="error-section">
                <div className="error-message">
                  <strong>Error:</strong> {extraction.error}
                </div>
              </section>
            )}

            <section className="action-section">
              <button
                type="button"
                className="btn-extract"
                onClick={handleStartExtraction}
                disabled={!canStartExtraction}
              >
                Start Extraction
              </button>
            </section>
          </>
        )}

        {/* Show progress during processing */}
        {isProcessing && (
          <section className="progress-section">
            <h2>Processing...</h2>
            <ProgressDisplay
              status={extraction.state === 'uploading' ? 'uploading' : 'processing'}
              progress={extraction.progress}
              total={extraction.total}
            />
            {extraction.state === 'uploading' && (
              <p className="uploading-text">Uploading files...</p>
            )}
          </section>
        )}

        {/* Show results when complete */}
        {isComplete && extraction.jobId && (
          <section className="results-section">
            <div className="results-header">
              <h2>Results</h2>
              <button
                type="button"
                className="btn-new-extraction"
                onClick={handleNewExtraction}
              >
                New Extraction
              </button>
            </div>

            <GraphPreview jobId={extraction.jobId} />
            <DownloadButtons jobId={extraction.jobId} />
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
