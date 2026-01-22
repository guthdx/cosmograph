// frontend/src/App.tsx
import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ExtractionOptions } from './components/ExtractionOptions';
import type { ExtractionOptions as Options } from './types';
import './App.css';

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<Options>({
    extractor: 'auto',
    title: 'Knowledge Graph',
    llmConfirmed: false,
  });
  const [isProcessing] = useState(false);

  const canStartExtraction = files.length > 0;

  const handleStartExtraction = () => {
    // Will be implemented in Plan 03
    console.log('Starting extraction with:', { files, options });
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Cosmograph</h1>
        <p>Document-to-Knowledge-Graph Service</p>
      </header>

      <main className="app-main">
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

        <section className="action-section">
          <button
            type="button"
            className="btn-extract"
            onClick={handleStartExtraction}
            disabled={!canStartExtraction || isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Start Extraction'}
          </button>
        </section>

        {/* Progress, results, and error display will be added in Plan 03 */}
      </main>
    </div>
  );
}

export default App;
