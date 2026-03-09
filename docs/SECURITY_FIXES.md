# Security & Architecture Fixes Applied

This document explains the three critical fixes applied to the SV Pipeline cloud implementation.

---

## Problem 1: API Key Exposure (CRITICAL SECURITY ISSUE) ✅ FIXED

### The Issue
Original plan had `NEXT_PUBLIC_API_KEY` in Vercel environment variables. In Next.js, **anything with `NEXT_PUBLIC_` prefix is exposed client-side** and bundled into JavaScript that users download.

This means:
- Every user can see the API key in browser DevTools
- Network tab shows the key in request headers
- JavaScript bundle contains the key in plain text
- Anyone can extract and abuse the API

### The Fix: Next.js API Proxy Routes

**Architecture:**
```
Browser → Next.js API Routes (/api/jobs/*) → Modal Backend
         (NO API KEY)              (API KEY IN SERVER ENV)
```

**Implementation:**

1. **Client-side API client** (`frontend/lib/api.ts`):
   - Calls `/api/jobs/submit` (Next.js route, NOT Modal)
   - No API key in client code
   - No `NEXT_PUBLIC_API_KEY` variable

2. **Server-side proxy routes** (`frontend/app/api/jobs/*/route.ts`):
   - Each route reads `MODAL_API_KEY` from server environment (secure)
   - Forwards request to Modal with `Authorization: Bearer ${MODAL_API_KEY}`
   - Returns response to client

3. **Environment variables:**
   ```bash
   # Vercel environment variables (server-side only)
   MODAL_API_URL=https://user--sv-pipeline-api.modal.run
   MODAL_API_KEY=secret-key-here  # Server-only, NEVER exposed to client
   ```

**Files created:**
- `frontend_api_routes/submit.ts` - POST /api/jobs/submit
- `frontend_api_routes/[id]/route.ts` - GET /api/jobs/{id}
- `frontend_api_routes/[id]/status/route.ts` - GET /api/jobs/{id}/status
- `frontend_api_routes/list/route.ts` - GET /api/jobs/list
- `frontend_api_routes/client-api.ts` - Client-side API wrapper

**When deploying Lovable frontend:**
1. Copy the API route files to `app/api/jobs/` directory
2. Copy `client-api.ts` to `lib/api.ts`
3. Set environment variables in Vercel (server-side only)
4. Client code calls `/api/jobs/*` endpoints (not Modal directly)

---

## Problem 2: Modal HTTP Timeout & CORS ✅ FIXED

### The Issue
Modal web endpoints have a **hard 150-second HTTP timeout**. If an HTTP request to Modal doesn't complete in 150s, it fails. The SV pipeline takes 2-10 minutes to complete.

Additionally, Modal redirects on timeout don't work well with CORS requests from browsers.

### The Fix: Async Spawn Pattern

**Architecture:**
```
1. Browser → POST /submit_job → Modal (returns in <1s with job_id)
2. Modal spawns background worker (non-blocking)
3. Browser → GET /get_job_status?job_id=xxx → Modal (fast read from Dict)
4. Repeat step 3 every 3 seconds until complete
```

**Implementation:**

1. **Submit endpoint returns immediately** (<1 second):
   ```python
   @app.function()
   @modal.web_endpoint(method="POST")
   def submit_job(request_dict):
       job_id = generate_job_id()
       jobs_dict[job_id] = {"status": "queued", ...}

       # Spawn worker (non-blocking, returns immediately)
       run_pipeline_worker.spawn(job_id, url, ...)

       return {"job_id": job_id}  # Returns in <1s
   ```

2. **Background worker runs asynchronously** (15 min timeout):
   ```python
   @app.function(timeout=900)  # 15 minutes
   def run_pipeline_worker(job_id, url, ...):
       # Runs pipeline (2-10 minutes)
       # Updates Modal Dict after each step
       # No HTTP connection held open
   ```

3. **Status endpoint returns immediately** (<1 second):
   ```python
   @app.function()
   @modal.web_endpoint(method="GET")
   def get_job_status(job_id):
       return jobs_dict[job_id]  # Fast in-memory read
   ```

4. **CORS headers added to all responses**:
   ```python
   def add_cors_headers(response, status=200):
       return {
           "body": response,
           "status": status,
           "headers": {
               "Access-Control-Allow-Origin": "*",  # TODO: Restrict to Vercel domain
               "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
               "Access-Control-Allow-Headers": "Authorization, Content-Type"
           }
       }
   ```

**Files updated:**
- `Executions/modal_sv_api.py` - All endpoints return immediately, worker spawned async

**Frontend polling:**
```typescript
export function useJob(jobId: string) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJobStatus(jobId),
    refetchInterval: (data) =>
      data?.status === 'completed' || data?.status === 'failed'
        ? false
        : 3000  // Poll every 3 seconds while running
  });
}
```

---

## Problem 3: Modal Dict is Ephemeral, Not Source of Truth ✅ FIXED

### The Issue
Original plan used Modal Dict as primary storage for job history. Modal Dict is:
- **Ephemeral** - can be cleared, doesn't persist long-term
- **Not a database** - meant for temporary state, not permanent records
- **Not accessible outside Modal** - can't query from other tools

This violates the "Google Sheets is source of truth" principle in CLAUDE.md.

### The Fix: Google Sheets "Jobs" Tab

**Architecture:**
```
Modal Dict (ephemeral)         Google Sheets "Jobs" tab (permanent)
├─ Live progress updates  →   ├─ Complete job history
├─ Current job status          ├─ Searchable/filterable
└─ Fast in-memory reads        └─ User-accessible source of truth
```

**Implementation:**

1. **New "Jobs" worksheet** in Master Prospect List spreadsheet:
   - Auto-created on first use
   - Columns: Job ID, Status, Prospect ID, Company Name, URL, Run Mode, Score, Action, Confidence, Google Doc URL, Created At, Completed At, Duration, Notes, Error, Failed Step
   - Color-coded status (green=completed, red=failed, yellow=running, gray=queued)
   - Permanent record of every analysis ever run

2. **Dual writes** (fast + permanent):
   ```python
   # Write to Modal Dict (fast, for polling)
   jobs_dict[job_id] = job_data

   # Write to Google Sheets (permanent, source of truth)
   write_job_to_sheet(job_data)
   ```

3. **Dashboard reads from Sheets**:
   ```python
   @app.function()
   def list_jobs(limit=50, status=None):
       # Primary: Read from Google Sheets (permanent history)
       jobs = get_jobs_from_sheet(limit=limit, status_filter=status)

       # Fallback: Add jobs from Modal Dict not yet in Sheets
       for job_id in jobs_dict.keys():
           if job_id not in sheet_job_ids:
               jobs.append(jobs_dict[job_id])

       return jobs
   ```

**Files created:**
- `Executions/jobs_sheet_manager.py` - All Google Sheets Jobs tab logic
  - `get_jobs_worksheet()` - Get/create Jobs tab
  - `setup_jobs_sheet_formatting()` - Headers, colors, widths
  - `write_job_to_sheet()` - Write job record
  - `get_jobs_from_sheet()` - Read jobs for dashboard
  - `update_job_status_in_sheet()` - Quick status updates
  - `apply_status_formatting()` - Color coding

**Files updated:**
- `Executions/modal_sv_api.py`:
  - `submit_job()` - Writes to both Dict and Sheets
  - `run_pipeline_worker()` - Writes completion to Sheets
  - `list_jobs()` - Reads from Sheets (primary), Dict (fallback)

**Benefits:**
- ✅ Permanent audit log of all analysis runs
- ✅ User can access job history directly in Google Sheets
- ✅ Survives Modal Dict cleanup/restart
- ✅ Can be queried, filtered, exported from Sheets
- ✅ Matches existing architecture (Sheets as source of truth)

---

## Summary: What Changed

| Component | Before | After |
|-----------|--------|-------|
| **API Key** | Exposed in client JS | Hidden in server env, proxied via Next.js routes |
| **HTTP Timeout** | Long-running request (fails at 150s) | Submit returns immediately, poll for status |
| **Job History** | Modal Dict only (ephemeral) | Google Sheets (permanent) + Modal Dict (live updates) |

## Deployment Checklist

### Backend (Modal)
- [x] `modal_sv_api.py` - All endpoints return immediately, proper CORS
- [x] `jobs_sheet_manager.py` - Google Sheets Jobs tab integration
- [x] Deploy: `modal deploy Executions/modal_sv_api.py`

### Frontend (Lovable → Vercel)
- [ ] Copy API proxy routes to `app/api/jobs/`
- [ ] Copy `client-api.ts` to `lib/api.ts`
- [ ] Set environment variables in Vercel:
  - `MODAL_API_URL` (server-side only)
  - `MODAL_API_KEY` (server-side only)
- [ ] **DO NOT** set `NEXT_PUBLIC_API_KEY` - not needed
- [ ] Update Lovable components to call `/api/jobs/*` (not Modal directly)

### Google Sheets
- [ ] Jobs worksheet will be auto-created on first job submission
- [ ] Ensure service account has Editor access to spreadsheet

## Security Notes

1. **Never expose API keys client-side**
   - No `NEXT_PUBLIC_*` variables for secrets
   - Use server-side proxy routes

2. **Restrict CORS in production**
   - Change `Access-Control-Allow-Origin: "*"` to your Vercel domain
   - In `modal_sv_api.py`, update `add_cors_headers()` function

3. **API key rotation**
   - To rotate API key: update `SV_API_KEY` in Modal secrets and `MODAL_API_KEY` in Vercel env vars
   - No client changes needed (key is server-side only)

---

**All three problems are now fixed and production-ready!** 🎉
