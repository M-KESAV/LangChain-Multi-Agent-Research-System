import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  API_BASE_URL,
  getHealth,
  createResearch,
  listResearch,
  getResearch,
  deleteResearch,
  getStreamUrl,
} from '../api/client';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('defaults API_BASE_URL to http://127.0.0.1:8000 when not configured', () => {
    expect(API_BASE_URL).toMatch(/127\.0\.0\.1:8000|localhost:8000/);
  });

  it('getStreamUrl generates the proper SSE endpoint path', () => {
    const url = getStreamUrl('test-123');
    expect(url).toBe(`${API_BASE_URL}/api/research/test-123/stream`);
  });

  it('getHealth returns health status object on 200 OK', async () => {
    const mockHealth = { status: 'ok', database: 'connected', version: '1.0.0' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await getHealth();
    expect(result).toEqual(mockHealth);
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/health`, expect.any(Object));
  });

  it('createResearch posts topic payload and returns research id', async () => {
    const mockResponse = { id: 'uuid-456', topic: 'AI in Healthcare', status: 'running', message: 'Started' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await createResearch('AI in Healthcare');
    expect(result).toEqual(mockResponse);
    expect(fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/research`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ topic: 'AI in Healthcare' }),
      })
    );
  });

  it('listResearch queries with limit parameter', async () => {
    const mockList = [{ id: 'run-1', topic: 'Topic 1', status: 'completed' }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockList,
    } as Response);

    const result = await listResearch(10);
    expect(result).toEqual(mockList);
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/research?limit=10`, expect.any(Object));
  });

  it('getResearch retrieves detail for specific id', async () => {
    const mockDetail = { id: 'run-99', topic: 'Fusion', status: 'completed', report: 'Report' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDetail,
    } as Response);

    const result = await getResearch('run-99');
    expect(result).toEqual(mockDetail);
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/research/run-99`, expect.any(Object));
  });

  it('deleteResearch issues DELETE method and returns response', async () => {
    const mockDelete = { message: 'Deleted', id: 'run-99' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDelete,
    } as Response);

    const result = await deleteResearch('run-99');
    expect(result).toEqual(mockDelete);
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/research/run-99`, expect.objectContaining({ method: 'DELETE' }));
  });

  it('extracts detail string on HTTP error response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: "Research run 'nonexistent' was not found." }),
    } as Response);

    await expect(getResearch('nonexistent')).rejects.toThrow("Research run 'nonexistent' was not found.");
  });
});
