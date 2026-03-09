// frontend/lib/api.ts
// Client-side API client - NO API KEYS, only calls our own Next.js routes

export const api = {
  /**
   * Submit a new analysis job
   */
  submitJob: async (data: {
    url: string;
    company_name?: string;
    run_mode: 'standard' | 'deep_canada';
    notes?: string;
  }) => {
    const response = await fetch('/api/jobs/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to submit job');
    }

    return response.json();
  },

  /**
   * Get job status (for polling)
   */
  getJobStatus: async (jobId: string) => {
    const response = await fetch(`/api/jobs/${jobId}/status`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch job status');
    }

    return response.json();
  },

  /**
   * Get full job details
   */
  getJob: async (jobId: string) => {
    const response = await fetch(`/api/jobs/${jobId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch job');
    }

    return response.json();
  },

  /**
   * List all jobs with pagination
   */
  listJobs: async (limit = 50, offset = 0) => {
    const response = await fetch(`/api/jobs/list?limit=${limit}&offset=${offset}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch jobs');
    }

    return response.json();
  },
};

// TypeScript types
export interface Job {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  url: string;
  company_name?: string;
  run_mode: string;
  notes?: string;
  created_at: string;
  last_updated: string;
  completed_at?: string;
  current_step?: string;
  current_step_name?: string;
  progress_pct?: number;
  prospect_id?: string;
  error?: string;
  results?: {
    overall_score: number;
    suggested_action: string;
    confidence_level: string;
    scores: Record<string, any>;
    google_doc_url: string;
    sheets_url: string;
  };
}
