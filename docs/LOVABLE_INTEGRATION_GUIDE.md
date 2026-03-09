# Lovable.ai Integration Guide
## How to Connect Your Lovable Frontend to the SV Pipeline Backend

This guide walks you through generating the UI in Lovable and connecting it to your Modal backend.

---

## Step 1: Generate UI in Lovable (2 hours)

### Upload Your UI Inspiration

1. Go to [Lovable.ai](https://lovable.dev)
2. Start a new project
3. Upload the 4 PDF files from `ui inspiration/` folder

### Prompt Lovable

Use this prompt (customize as needed):

```
Create a venture capital deal flow analysis dashboard called "SV Analyzer" with these pages:

PAGE 1: Home / Run Analysis
- Clean centered layout with card-based design
- Header with "SV Analyzer" branding and navigation
- Hero section with tagline: "Streamline your deal flow with automated company analysis and scoring"
- Form with these fields:
  * Company URL (required) - text input
  * Company Name (optional) - text input
  * Run Mode dropdown - options: "Standard" (default) or "Deep Canada"
  * Notes/Context (optional) - textarea
  * "Run Analysis" button (primary action)
- Feature cards section explaining how it works (Fast Analysis, Composite Scoring, Rich Profiles, Real-time Status)

PAGE 2: Dashboard
- Page title: "Dashboard" with subtitle "View and manage all analysis runs"
- Search bar: "Search by company name or URL"
- Filter dropdowns: Status (All/Complete/Running/Queued/Failed), Decision (All/Strong Pass/Conditional Pass)
- Refresh button
- Data table with columns:
  * Company (name + URL with external link icon)
  * Status (badge with color: Complete=green, Running=yellow, Queued=gray, Failed=red)
  * Score (numeric, color-coded: ≥4 green, ≥3 yellow, <3 red)
  * Decision (Strong Pass=green with thumbs-up, Conditional Pass=yellow with caution)
  * Updated (relative timestamp like "1 day ago")
- Click row to navigate to detail page
- Pagination showing "X of Y runs"

PAGE 3: Job Detail
- Back to Dashboard navigation link
- Company header card with:
  * Company name (large bold)
  * Status badge next to name
  * Website URL with external link
  * 4-metric grid: SCORE (large number), DECISION (badge), MODE (tag), UPDATED (timestamp)
- While running: Progress bar + current step indicator
- When complete:
  * Score cards for 5 dimensions (Problem Clarity, MVP Speed, Defensible Wedge, Studio Fit, Canada Fit)
  * Actions card with buttons: "Open Profile Doc", "Open in Sheets", "Download JSON"
  * Run Information card with Job ID, Created, Last Updated, Notes

PAGE 4: Documents
- Page title: "Documents" with subtitle "Browse completed company profile documents"
- Search bar
- Refresh button
- Grid of document cards showing: doc icon, title, company name, date
- Click card to open Google Doc

DESIGN SPECS:
- Color scheme: Green (#22C55E) for success, Yellow/Amber for warnings, Red for errors, Gray for neutral
- Card-based layout with rounded corners and subtle shadows
- Clean white background
- Use Tailwind CSS
- Icons from lucide-react
- Responsive mobile-friendly design
- Professional, functional aesthetic for VC tool

FUNCTIONALITY:
- Form submission calls API to submit job
- Real-time polling for job status updates (every 3 seconds)
- Status badges with icons and colors
- External link indicators for Google Docs/Sheets
- Search and filter on dashboard
- Client-side routing (React Router or Next.js)
```

### Iterate on Design

- Lovable will generate the UI
- Refine by chatting: "Make the score cards bigger", "Change the color scheme", etc.
- Match the inspiration PDFs as closely as possible

---

## Step 2: Export from Lovable

1. Click "Export" or "Download" in Lovable
2. You'll get a Next.js or Vite project with all components
3. Extract the ZIP file

---

## Step 3: Integrate API Client (30 minutes)

### Copy API Proxy Routes

Copy the API proxy files from this repository to your Lovable export:

```bash
# If Lovable exported Next.js (App Router):
cp frontend_api_routes/submit.ts lovable-export/app/api/jobs/submit/route.ts
cp frontend_api_routes/[id]/route.ts lovable-export/app/api/jobs/[id]/route.ts
cp frontend_api_routes/[id]/status/route.ts lovable-export/app/api/jobs/[id]/status/route.ts
cp frontend_api_routes/list/route.ts lovable-export/app/api/jobs/list/route.ts

# Copy client API wrapper:
cp frontend_api_routes/client-api.ts lovable-export/lib/api.ts
```

**Important:** If Lovable used a different framework (Vite, Pages Router), you'll need to adapt the routes. The key principle:
- **Client code calls `/api/jobs/*`** (your own Next.js routes)
- **Next.js routes call Modal backend** with server-side API key

### Update Lovable Components to Use API

Find where Lovable generated the form submission logic and update it:

**Before (Lovable's placeholder):**
```typescript
const handleSubmit = async (data) => {
  // TODO: Connect to backend
  console.log('Submitting:', data);
};
```

**After (using our API client):**
```typescript
import { api } from '@/lib/api';
import { useNavigate } from 'react-router-dom';  // or next/navigation

const handleSubmit = async (data) => {
  try {
    const result = await api.submitJob({
      url: data.url,
      company_name: data.companyName,
      run_mode: data.runMode,  // 'standard' or 'deep_canada'
      notes: data.notes
    });

    // Navigate to job detail page
    navigate(`/jobs/${result.job_id}`);
  } catch (error) {
    console.error('Failed to submit job:', error);
    // Show error to user
  }
};
```

### Add Polling Hook

If Lovable didn't include React Query, add it:

```bash
cd lovable-export
npm install @tanstack/react-query
```

Create polling hook in `lovable-export/hooks/useJob.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api, Job } from '@/lib/api';

export function useJob(jobId: string | null) {
  return useQuery<Job>({
    queryKey: ['job', jobId],
    queryFn: () => jobId ? api.getJobStatus(jobId) : Promise.reject(),
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Stop polling when complete or failed
      if (!data) return false;
      return data.status === 'completed' || data.status === 'failed'
        ? false
        : 3000;  // Poll every 3 seconds
    }
  });
}

export function useJobs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['jobs', limit, offset],
    queryFn: () => api.listJobs(limit, offset),
    refetchInterval: 10000  // Refresh list every 10 seconds
  });
}
```

### Update Job Detail Page

Find the job detail component Lovable generated and add polling:

```typescript
'use client';  // If Next.js App Router

import { useParams } from 'next/navigation';  // or react-router-dom
import { useJob } from '@/hooks/useJob';

export default function JobDetailPage() {
  const { id } = useParams();
  const { data: job, isLoading, error } = useJob(id as string);

  if (isLoading) return <div>Loading job...</div>;
  if (error) return <div>Error loading job</div>;
  if (!job) return <div>Job not found</div>;

  return (
    <div>
      <h1>{job.company_name || 'Company Analysis'}</h1>

      {/* Status badge */}
      <StatusBadge status={job.status} />

      {/* Progress bar (if running) */}
      {job.status === 'running' && (
        <div>
          <ProgressBar percent={job.progress_pct} />
          <p>{job.current_step_name}</p>
        </div>
      )}

      {/* Results (if completed) */}
      {job.status === 'completed' && job.results && (
        <div>
          <ScoreCard scores={job.results.scores} />
          <a href={job.results.google_doc_url} target="_blank">
            Open Profile Doc
          </a>
          <a href={job.results.sheets_url} target="_blank">
            Open in Sheets
          </a>
        </div>
      )}

      {/* Error (if failed) */}
      {job.status === 'failed' && (
        <div className="bg-red-100 p-4 rounded">
          <p>Failed at step: {job.failed_step}</p>
          <p>Error: {job.error}</p>
        </div>
      )}
    </div>
  );
}
```

### Update Dashboard Page

```typescript
'use client';

import { useJobs } from '@/hooks/useJob';

export default function DashboardPage() {
  const { data, isLoading } = useJobs();

  if (isLoading) return <div>Loading jobs...</div>;

  return (
    <div>
      <h1>Dashboard</h1>

      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Status</th>
            <th>Score</th>
            <th>Decision</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {data?.jobs.map((job) => (
            <tr key={job.job_id} onClick={() => navigate(`/jobs/${job.job_id}`)}>
              <td>
                <div>{job.company_name}</div>
                <div className="text-sm text-gray-500">{job.url}</div>
              </td>
              <td><StatusBadge status={job.status} /></td>
              <td>
                {job.results?.overall_score && (
                  <ScoreBadge score={job.results.overall_score} />
                )}
              </td>
              <td>
                {job.results?.suggested_action && (
                  <DecisionBadge action={job.results.suggested_action} />
                )}
              </td>
              <td>{formatRelativeTime(job.last_updated)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Step 4: Environment Variables

Create `.env.local` in your Lovable export:

```bash
# Server-side only (NEVER use NEXT_PUBLIC_ for secrets)
MODAL_API_URL=https://youruser--sv-pipeline-api.modal.run
MODAL_API_KEY=your-api-key-here
```

**Important:**
- ✅ **DO NOT** use `NEXT_PUBLIC_` prefix for API keys
- ✅ API key is only accessed by server-side API routes
- ✅ Client code never sees the API key

---

## Step 5: Deploy to Vercel (15 minutes)

### Install Vercel CLI

```bash
npm install -g vercel
```

### Deploy

```bash
cd lovable-export
vercel --prod
```

### Set Environment Variables in Vercel

Go to your Vercel project dashboard → Settings → Environment Variables:

Add:
- `MODAL_API_URL` = `https://youruser--sv-pipeline-api.modal.run`
- `MODAL_API_KEY` = (paste your API key)

**Scope:** Production, Preview, Development

### Redeploy

```bash
vercel --prod
```

---

## Step 6: Update CORS in Modal (5 minutes)

Once you have your Vercel domain, update the CORS settings in Modal:

Edit `Executions/modal_sv_api.py`:

```python
def add_cors_headers(response_dict: dict, status: int = 200):
    """Add CORS headers to response."""
    return {
        "body": response_dict,
        "status": status,
        "headers": {
            # ✅ Update this to your Vercel domain
            "Access-Control-Allow-Origin": "https://your-app.vercel.app",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    }
```

Redeploy Modal:

```bash
modal deploy Executions/modal_sv_api.py
```

---

## Testing Checklist

### Local Testing (Before Deploy)

```bash
cd lovable-export
npm install
npm run dev
```

- [ ] Home page form submits successfully
- [ ] Redirects to job detail page after submit
- [ ] Job detail page shows "queued" status
- [ ] Progress updates every 3 seconds
- [ ] Progress bar advances through steps
- [ ] Completed job shows scores
- [ ] Google Doc link works
- [ ] Google Sheets link works
- [ ] Dashboard shows all jobs
- [ ] Search and filter work

### Production Testing (After Deploy)

- [ ] Submit test job via Vercel URL
- [ ] Real-time status updates work
- [ ] No CORS errors in browser console
- [ ] API key not visible in Network tab
- [ ] API key not visible in JavaScript bundle
- [ ] Failed jobs show error message
- [ ] Multiple concurrent jobs work

---

## Troubleshooting

### "CORS policy: No 'Access-Control-Allow-Origin' header"

**Fix:** Update `Access-Control-Allow-Origin` in `modal_sv_api.py` to match your Vercel domain.

### "Failed to fetch" or Network Error

**Possible causes:**
1. Modal API is down (check `modal app logs sv-pipeline-api`)
2. Wrong `MODAL_API_URL` in environment variables
3. API key is wrong

**Fix:** Check Vercel logs and Modal logs for errors.

### Job stays in "queued" status forever

**Possible causes:**
1. Background worker failed to spawn
2. Pipeline script error

**Fix:** Check Modal logs:
```bash
modal app logs sv-pipeline-api
```

### API key visible in browser

**This is critical!** If you can see the API key in:
- Browser DevTools → Network tab
- Browser DevTools → Sources tab (JavaScript files)

**Fix:**
1. Ensure you're using `/api/jobs/*` routes (NOT calling Modal directly)
2. Ensure API client doesn't have API key in code
3. Ensure environment variable is **NOT** prefixed with `NEXT_PUBLIC_`

---

## Architecture Diagram

```
┌─────────────────┐
│  User Browser   │
└────────┬────────┘
         │
         │ Calls /api/jobs/* (NO API KEY)
         ▼
┌──────────────────────────────┐
│  Vercel (Next.js Frontend)   │
│  ┌────────────────────────┐  │
│  │ API Routes (/api/jobs) │  │ ← API KEY here (server-side)
│  └───────────┬────────────┘  │
└──────────────┼───────────────┘
               │
               │ Adds Bearer token
               ▼
┌──────────────────────────────┐
│  Modal (Backend API)         │
│  ┌────────────────────────┐  │
│  │ Web Endpoints          │  │
│  │ - submit_job           │  │
│  │ - get_job_status       │  │
│  │ - list_jobs            │  │
│  └───────────┬────────────┘  │
│              │                │
│  ┌───────────▼────────────┐  │
│  │ Background Worker      │  │
│  │ - run_pipeline_worker  │  │
│  └───────────┬────────────┘  │
└──────────────┼───────────────┘
               │
               │ Updates
               ▼
┌──────────────────────────────┐
│  Storage Layer               │
│  ├─ Modal Dict (ephemeral)   │
│  └─ Google Sheets (permanent)│
└──────────────────────────────┘
```

---

## Summary

1. **Generate UI** in Lovable with your PDFs
2. **Copy API routes** to `app/api/jobs/`
3. **Update components** to use API client
4. **Add polling hooks** with React Query
5. **Set environment variables** (server-side only)
6. **Deploy to Vercel**
7. **Update CORS** in Modal
8. **Test end-to-end**

**Total time: ~3 hours** (2 hours Lovable, 1 hour integration)

**Key principle:** Client code NEVER has API keys. All API calls go through Next.js server routes that add authentication.

🎉 **You now have a production-ready, secure SV Pipeline web app!**
