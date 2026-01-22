// frontend/src/hooks/useExtraction.ts
import { useState, useCallback } from 'react';
import { createExtraction, ApiError } from '../services/api';
import { useProgress } from './useProgress';
import type { ExtractionOptions } from '../types';

type ExtractionState = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

interface UseExtractionResult {
  state: ExtractionState;
  jobId: string | null;
  progress: number;
  total: number;
  error: string | null;
  startExtraction: (files: File[], options: ExtractionOptions) => Promise<void>;
  reset: () => void;
}

/**
 * Hook to manage the full extraction workflow.
 *
 * Handles: file upload -> job creation -> progress tracking -> completion.
 */
export function useExtraction(): UseExtractionResult {
  const [state, setState] = useState<ExtractionState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const progressData = useProgress(jobId);

  // Sync progress state to extraction state
  const derivedState = (): ExtractionState => {
    if (state === 'uploading') return 'uploading';
    if (progressData.isComplete) return 'completed';
    if (progressData.error || state === 'failed') return 'failed';
    if (jobId && progressData.status === 'processing') return 'processing';
    if (jobId && progressData.status === 'pending') return 'processing';
    return state;
  };

  const startExtraction = useCallback(async (files: File[], options: ExtractionOptions) => {
    // Reset previous state
    setError(null);
    setJobId(null);
    progressData.reset();
    setState('uploading');

    try {
      const response = await createExtraction(
        files,
        options.extractor,
        options.title,
        options.llmConfirmed
      );

      setJobId(response.job_id);
      setState('processing');
    } catch (e) {
      setState('failed');
      if (e instanceof ApiError) {
        setError(e.message);
      } else if (e instanceof Error) {
        setError(e.message);
      } else {
        setError('An unexpected error occurred');
      }
    }
  }, [progressData]);

  const reset = useCallback(() => {
    setState('idle');
    setJobId(null);
    setError(null);
    progressData.reset();
  }, [progressData]);

  return {
    state: derivedState(),
    jobId,
    progress: progressData.progress,
    total: progressData.total,
    error: error || progressData.error,
    startExtraction,
    reset,
  };
}
