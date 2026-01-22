// frontend/src/hooks/useProgress.ts
import { useEffect, useState, useCallback } from 'react';
import type { JobStatus } from '../types';

interface ProgressState {
  status: JobStatus;
  progress: number;
  total: number;
  isComplete: boolean;
  error: string | null;
}

const initialState: ProgressState = {
  status: 'pending',
  progress: 0,
  total: 0,
  isComplete: false,
  error: null,
};

/**
 * Hook to stream extraction progress via Server-Sent Events.
 *
 * Connects to /api/extract/{jobId}/progress and receives progress, complete, and error events.
 * Automatically closes connection when job completes or fails.
 */
export function useProgress(jobId: string | null) {
  const [state, setState] = useState<ProgressState>(initialState);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  useEffect(() => {
    if (!jobId) {
      reset();
      return;
    }

    const eventSource = new EventSource(`/api/extract/${jobId}/progress`);

    eventSource.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse(event.data);
        setState(prev => ({
          ...prev,
          status: data.status,
          progress: data.progress,
          total: data.total,
        }));
      } catch (e) {
        console.error('Failed to parse progress event:', e);
      }
    });

    eventSource.addEventListener('complete', () => {
      setState(prev => ({ ...prev, status: 'completed', isComplete: true }));
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      // Check if it's a data event (server-sent error) vs connection error
      if (event instanceof MessageEvent && event.data) {
        try {
          const data = JSON.parse(event.data);
          setState(prev => ({ ...prev, status: 'failed', error: data.error }));
        } catch (e) {
          setState(prev => ({ ...prev, status: 'failed', error: 'Unknown error occurred' }));
        }
      }
      eventSource.close();
    });

    // Connection error handler (network issues, server down)
    eventSource.onerror = () => {
      // EventSource auto-reconnects on some errors; only close if readyState is CLOSED
      if (eventSource.readyState === EventSource.CLOSED) {
        setState(prev => ({
          ...prev,
          status: 'failed',
          error: 'Connection lost. Please try again.',
        }));
      }
    };

    // Cleanup on unmount or jobId change
    return () => {
      eventSource.close();
    };
  }, [jobId, reset]);

  return { ...state, reset };
}
