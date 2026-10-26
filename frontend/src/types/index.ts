export type ResearchStage =
  | 'idle'
  | 'running'
  | 'started'
  | 'searching'
  | 'reading'
  | 'writing'
  | 'reviewing'
  | 'completed'
  | 'failed';

export interface HealthStatus {
  status: string;
  database: string;
  version: string;
}

export interface ResearchCreateResponse {
  id: string;
  topic: string;
  status: string;
  message: string;
}

export interface SourceItem {
  title?: string;
  url: string;
  snippet?: string;
  status?: 'scraped' | 'discovered' | 'failed';
  error?: string;
}

export interface ResearchSummary {
  id: string;
  topic: string;
  status: 'running' | 'completed' | 'failed';
  report?: string | null;
  feedback?: string | null;
  sources?: SourceItem[];
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchDetail {
  id: string;
  topic: string;
  status: 'running' | 'completed' | 'failed';
  search_results?: string | null;
  scraped_content?: string | null;
  report?: string | null;
  feedback?: string | null;
  sources?: SourceItem[];
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SSEProgressEvent {
  stage: ResearchStage;
  id?: string;
  topic?: string;
  message?: string;
  report?: string;
  feedback?: string;
  error?: string;
  timestamp?: string;
}
