// frontend/src/components/ErrorDisplay.tsx
import './ErrorDisplay.css';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

/**
 * Reusable error display component.
 *
 * Shows error message with optional dismiss and retry actions.
 */
export function ErrorDisplay({ title = 'Error', message, onDismiss, onRetry }: ErrorDisplayProps) {
  return (
    <div className="error-display" role="alert">
      <div className="error-content">
        <strong className="error-title">{title}</strong>
        <p className="error-message">{message}</p>
      </div>
      {(onDismiss || onRetry) && (
        <div className="error-actions">
          {onRetry && (
            <button type="button" className="btn-retry" onClick={onRetry}>
              Try Again
            </button>
          )}
          {onDismiss && (
            <button type="button" className="btn-dismiss" onClick={onDismiss}>
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  );
}
