import type {
  HealthStatus,
  ResearchCreateResponse,
  ResearchSummary,
  ResearchDetail,
} from '../types';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data && typeof data.detail === 'string') {
        errorDetail = data.detail;
      } else if (data && data.detail && typeof data.detail === 'object') {
        errorDetail = JSON.stringify(data.detail);
      }
    } catch {
      // Body not JSON
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/api/health`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<HealthStatus>(res);
}

export async function createResearch(topic: string): Promise<ResearchCreateResponse> {
  const res = await fetch(`${API_BASE_URL}/api/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ topic }),
  });
  return handleResponse<ResearchCreateResponse>(res);
}

export async function listResearch(limit = 20): Promise<ResearchSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/research?limit=${limit}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<ResearchSummary[]>(res);
}

export async function getResearch(id: string): Promise<ResearchDetail> {
  const res = await fetch(`${API_BASE_URL}/api/research/${encodeURIComponent(id)}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<ResearchDetail>(res);
}

export async function deleteResearch(id: string): Promise<{ message: string; id?: string }> {
  const res = await fetch(`${API_BASE_URL}/api/research/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<{ message: string; id?: string }>(res);
}

export function getStreamUrl(id: string): string {
  return `${API_BASE_URL}/api/research/${encodeURIComponent(id)}/stream`;
}
