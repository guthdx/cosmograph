// frontend/src/components/LlmConfirmDialog.tsx
import './LlmConfirmDialog.css';

interface LlmConfirmDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function LlmConfirmDialog({ isOpen, onConfirm, onCancel }: LlmConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div className="dialog" onClick={e => e.stopPropagation()}>
        <h3>Enable AI Extraction?</h3>
        <p>
          <strong>Data Sovereignty Notice:</strong> Using AI extraction will send your
          document content to the Claude API (Anthropic).
        </p>
        <p>Please confirm you have authorization to send this data externally.</p>
        <div className="dialog-actions">
          <button type="button" className="btn-cancel" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="btn-confirm" onClick={onConfirm}>
            I Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
