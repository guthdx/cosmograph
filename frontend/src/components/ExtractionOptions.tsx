// frontend/src/components/ExtractionOptions.tsx
import { useState } from 'react';
import type { ExtractorType, ExtractionOptions as Options } from '../types';
import { LlmConfirmDialog } from './LlmConfirmDialog';
import './ExtractionOptions.css';

interface ExtractionOptionsProps {
  options: Options;
  onChange: (options: Options) => void;
  disabled?: boolean;
}

const EXTRACTOR_DESCRIPTIONS: Record<ExtractorType, string> = {
  auto: 'Automatically detect document type',
  legal: 'Legal documents (codes, ordinances)',
  text: 'Plain text and markdown',
  generic: 'Pattern-based extraction',
  pdf: 'PDF documents',
  llm: 'AI-powered extraction (Claude)',
};

export function ExtractionOptions({ options, onChange, disabled }: ExtractionOptionsProps) {
  const [showLlmDialog, setShowLlmDialog] = useState(false);
  const [pendingLlmConfirm, setPendingLlmConfirm] = useState(false);

  const handleExtractorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newExtractor = e.target.value as ExtractorType;

    if (newExtractor === 'llm') {
      // Show confirmation dialog for LLM (data sovereignty gate)
      setShowLlmDialog(true);
      setPendingLlmConfirm(true);
    } else {
      onChange({ ...options, extractor: newExtractor, llmConfirmed: false });
    }
  };

  const handleLlmConfirm = () => {
    setShowLlmDialog(false);
    setPendingLlmConfirm(false);
    onChange({ ...options, extractor: 'llm', llmConfirmed: true });
  };

  const handleLlmCancel = () => {
    setShowLlmDialog(false);
    setPendingLlmConfirm(false);
    // Keep previous extractor selection
  };

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...options, title: e.target.value });
  };

  return (
    <div className="extraction-options">
      <div className="option-group">
        <label htmlFor="extractor">Extraction Method</label>
        <select
          id="extractor"
          value={pendingLlmConfirm ? options.extractor : options.extractor}
          onChange={handleExtractorChange}
          disabled={disabled}
        >
          <option value="auto">Auto-detect</option>
          <option value="legal">Legal Documents</option>
          <option value="text">Plain Text</option>
          <option value="generic">Pattern-based</option>
          <option value="pdf">PDF</option>
          <option value="llm">AI (Claude) - requires confirmation</option>
        </select>
        <p className="option-description">{EXTRACTOR_DESCRIPTIONS[options.extractor]}</p>
      </div>

      <div className="option-group">
        <label htmlFor="title">Graph Title</label>
        <input
          id="title"
          type="text"
          value={options.title}
          onChange={handleTitleChange}
          placeholder="Knowledge Graph"
          disabled={disabled}
        />
      </div>

      {options.extractor === 'llm' && options.llmConfirmed && (
        <div className="llm-confirmed-notice">
          AI extraction enabled - document content will be sent to Claude API
        </div>
      )}

      <LlmConfirmDialog
        isOpen={showLlmDialog}
        onConfirm={handleLlmConfirm}
        onCancel={handleLlmCancel}
      />
    </div>
  );
}
