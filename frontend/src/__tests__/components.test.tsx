import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../components/Header';
import { ResearchForm } from '../components/ResearchForm';
import { ProgressTimeline } from '../components/ProgressTimeline';
import { ReportViewer } from '../components/ReportViewer';
import type { HealthStatus, ResearchDetail, SSEProgressEvent } from '../types';

describe('Frontend UI Components', () => {
  it('Header renders system title and health status when connected', () => {
    const mockHealth: HealthStatus = {
      status: 'ok',
      database: 'connected',
      version: '1.0.0',
    };

    render(
      <Header
        health={mockHealth}
        healthLoading={false}
        onNewResearch={vi.fn()}
        onToggleSidebar={vi.fn()}
        isSidebarOpen={false}
      />
    );

    expect(screen.getByText('Multi-Agent AI')).toBeDefined();
    expect(screen.getByText('Backend & SQLite Ready')).toBeDefined();
    expect(screen.getByText('v1.0.0')).toBeDefined();
  });

  it('ResearchForm prevents empty submissions and calls onSubmit on valid topic', () => {
    const handleSubmit = vi.fn();
    render(<ResearchForm onSubmit={handleSubmit} isLoading={false} />);

    // Click submit without entering topic
    const submitBtn = screen.getByRole('button', { name: /Start Autonomous Research/i });
    expect(submitBtn).toBeDefined();

    // Select a sample prompt
    const samplePrompt = screen.getByText(/Impact of Autonomous AI Agents/i);
    fireEvent.click(samplePrompt);

    // Topic input should now have the sample prompt
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toContain('Impact of Autonomous AI Agents');

    // Submit form
    fireEvent.click(submitBtn);
    expect(handleSubmit).toHaveBeenCalledWith(textarea.value);
  });

  it('ProgressTimeline renders stage steps and backend progress message', () => {
    const mockEvents: SSEProgressEvent[] = [
      {
        stage: 'searching',
        message: 'Search agent is searching the web for relevant sources...',
        timestamp: new Date().toISOString(),
      },
    ];

    render(
      <ProgressTimeline
        currentStage="searching"
        topic="Solid-State Batteries"
        events={mockEvents}
      />
    );

    expect(screen.getByText('Solid-State Batteries')).toBeDefined();
    expect(screen.getByText('Web Discovery')).toBeDefined();
    expect(screen.getByText('Search agent is searching the web for relevant sources...')).toBeDefined();
    expect(screen.getByText('Active')).toBeDefined();
  });

  it('ReportViewer renders markdown content and extracted sources', () => {
    const mockDetail: ResearchDetail = {
      id: 'test-report-id',
      topic: 'Fusion Energy 2026',
      status: 'completed',
      search_results: 'Discovered https://example.com/fusion-breakthrough and notes.',
      scraped_content: 'Full article text from https://energy.org/fusion-report',
      report: '# Executive Summary\n\nFusion energy is advancing rapidly with **magnet** technology.\n\n- Milestone 1\n- Milestone 2',
      feedback: 'Score: 9/10 - Well-structured analysis with solid citations.',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<ReportViewer research={mockDetail} onDelete={vi.fn()} />);

    expect(screen.getByText('Fusion Energy 2026')).toBeDefined();
    expect(screen.getByText('Executive Summary')).toBeDefined();
    expect(screen.getByText('Milestone 1')).toBeDefined();
    expect(screen.getByText('Milestone 2')).toBeDefined();

    // Switch to Critic tab
    const criticTab = screen.getByRole('button', { name: /Critic Evaluation/i });
    fireEvent.click(criticTab);
    expect(screen.getByText(/Critic Agent Review & Recommendations/i)).toBeDefined();
    expect(screen.getByText(/Score: 9\/10/i)).toBeDefined();

    // Switch to Sources tab
    const sourcesTab = screen.getByRole('button', { name: /Sources & Intelligence/i });
    fireEvent.click(sourcesTab);
    expect(screen.getAllByText('https://example.com/fusion-breakthrough').length).toBeGreaterThan(0);
    expect(screen.getAllByText('https://energy.org/fusion-report').length).toBeGreaterThan(0);
  });

  it('ReportViewer renders structured sources with titles and status badges', () => {
    const mockDetailWithSources: ResearchDetail = {
      id: 'test-structured-id',
      topic: 'Quantum Computing 2026',
      status: 'completed',
      sources: [
        {
          title: 'Nature Quantum Advances',
          url: 'https://nature.com/articles/quantum-2026',
          snippet: 'Major breakthrough in error correction codes.',
          status: 'scraped',
        },
        {
          title: 'MIT Tech Review: Quantum Algorithms',
          url: 'https://technologyreview.com/quantum-algorithms',
          snippet: 'Commercial viability reached in simulation.',
          status: 'discovered',
        },
      ],
      report: '# Quantum Computing Report\n\nQuantum algorithms are advancing [1].',
      feedback: 'Score: 9/10',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<ReportViewer research={mockDetailWithSources} onDelete={vi.fn()} />);

    // Switch to Sources tab
    const sourcesTab = screen.getByRole('button', { name: /Sources & Intelligence \(2\)/i });
    fireEvent.click(sourcesTab);

    expect(screen.getByText('Nature Quantum Advances')).toBeDefined();
    expect(screen.getByText('https://nature.com/articles/quantum-2026')).toBeDefined();
    expect(screen.getByText('Scraped')).toBeDefined();

    expect(screen.getByText('MIT Tech Review: Quantum Algorithms')).toBeDefined();
    expect(screen.getByText('https://technologyreview.com/quantum-algorithms')).toBeDefined();
    expect(screen.getByText('Discovered')).toBeDefined();
  });
});
