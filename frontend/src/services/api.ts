// frontend/src/services/api.ts

import type { JobResponse, GraphResponse, ExtractorType } from '../types';

const API_BASE = '/api';

/**
 * API Error class for handling backend error responses.
 */
export class ApiError extends Error {
  status: number;
  errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
  }
}

/**
 * Create an extraction job from files.
 *
 * IMPORTANT: Do NOT set Content-Type header - browser sets it with boundary for FormData.
 */
export async function createExtraction(
  files: File[],
  extractor: ExtractorType = 'auto',
  title: string = 'Knowledge Graph',
  llmConfirmed: boolean = false
): Promise<JobResponse> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('extractor', extractor);
  formData.append('title', title);
  formData.append('llm_confirmed', String(llmConfirmed));

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(
      error.detail || 'Extraction failed',
      response.status,
      error.error_code
    );
  }

  return response.json();
}

/**
 * Get the status of an extraction job.
 */
export async function getJobStatus(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE}/extract/${jobId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(
      error.detail || 'Failed to get job status',
      response.status,
      error.error_code
    );
  }

  return response.json();
}

/**
 * Get the extracted graph data.
 */
export async function getGraph(jobId: string): Promise<GraphResponse> {
  const response = await fetch(`${API_BASE}/graph/${jobId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(
      error.detail || 'Failed to get graph',
      response.status,
      error.error_code
    );
  }

  return response.json();
}

/**
 * Get the URL for downloading the HTML visualization.
 */
export function getDownloadHtmlUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}`;
}

/**
 * Get the URL for downloading the CSV ZIP archive.
 */
export function getDownloadCsvUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}/csv`;
}
