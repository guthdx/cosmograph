// frontend/src/types/index.ts

/**
 * TypeScript types matching backend Pydantic schemas.
 * Source: src/cosmograph/api/schemas.py
 */

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type ExtractorType = 'auto' | 'legal' | 'text' | 'generic' | 'pdf' | 'llm';

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  total: number;
  created_at: string;
  error: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  category: string;
  description?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface GraphResponse {
  title: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    nodes: number;
    edges: number;
  };
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface ExtractionOptions {
  extractor: ExtractorType;
  title: string;
  llmConfirmed: boolean;
}
