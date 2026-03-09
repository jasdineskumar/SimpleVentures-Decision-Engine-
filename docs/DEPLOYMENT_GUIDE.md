# Complete Deployment Guide
## SV Pipeline Cloud Function + Lovable Frontend

This guide walks you through deploying the entire system from scratch.

---

## ✅ Pre-Deployment Checklist

Before you begin, ensure you have:

- [ ] Modal account created ([modal.com](https://modal.com))
- [ ] Vercel account created ([vercel.com](https://vercel.com))
- [ ] Google Cloud account with a project created
- [ ] OpenAI API key
- [ ] Firecrawl API key
- [ ] Access to the Google Sheet (Master Prospect List)

---

## Phase 1: Google Service Account Setup (30 minutes)

### Step 1.1: Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project or create a new one
3. Navigate to: **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**
5. Fill in:
   - **Name**: `sv-pipeline-service`
   - **Description**: `Service account for SV Pipeline automation`
6. Click **Create and Continue**
7. **Skip role assignment** (we'll use direct sharing instead)
8. Click **Done**

### Step 1.2: Generate JSON Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** → **Create New Key**
4. Select **JSON** format
5. Click **Create**
6. **Save the downloaded file** as `service-account.json` in your project root
7. **IMPORTANT**: Copy the service account email (looks like `sv-pipeline-service@your-project.iam.gserviceaccount.com`)

### Step 1.3: Share Google Resources

1. **Share Google Sheet**:
   - Open your Master Prospect List spreadsheet
   - Click **Share**
   - Paste the service account email
   - Set permission to **Editor**
   - Uncheck "Notify people"
   - Click **Share**

2. **Share Google Drive Folder** (where docs are created):
   - Open Google Drive
   - Navigate to the folder where you want profile docs created (or create a new folder called "SV Profiles")
   - Right-click → **Share**
   - Paste the service account email
   - Set permission to **Editor**
   - Click **Share**

### Step 1.4: Test Service Account Locally

```bash
# Set environment variable
export GOOGLE_SERVICE_ACCOUNT_JSON=./service-account.json

# Test authentication
python Executions/google_auth_cloud.py
```

You should see:
```
✓ Successfully loaded credentials
✓ Service account email: sv-pipeline-service@your-project.iam.gserviceaccount.com
✓ Scopes: spreadsheets, documents, drive
✓ ALL TESTS PASSED - Ready for use!
```

---

## Phase 2: Modal Backend Deployment (45 minutes)

### Step 2.1: Install Modal CLI

```bash
pip install modal
```

### Step 2.2: Authenticate with Modal

```bash
modal token new
```

This will open your browser for authentication.

### Step 2.3: Prepare Service Account JSON for Modal

Open `service-account.json` and copy its **entire contents** (the whole JSON object).

### Step 2.4: Create Modal Secrets

```bash
# Generate a secure API key
openssl rand -hex 32

# Save this key somewhere safe - you'll need it for Vercel
```

Now create the Modal secret:

```bash
modal secret create sv-secrets \
  OPENAI_API_KEY="sk-your-openai-key-here" \
  FIRECRAWL_API_KEY="fc-your-firecrawl-key-here" \
  GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT='paste-entire-json-content-here' \
  MASTER_PROSPECT_LIST_SHEET_ID="your-sheet-id-here" \
  SV_API_KEY="your-generated-api-key-from-above"
```

**Important**:
- Replace `OPENAI_API_KEY` with your actual OpenAI key
- Replace `FIRECRAWL_API_KEY` with your actual Firecrawl key
- For `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT`, paste the **entire JSON content** from `service-account.json` (including curly braces)
- For `MASTER_PROSPECT_LIST_SHEET_ID`, get the ID from your Google Sheet URL:
  - URL: `https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit`
  - ID: `YOUR_GOOGLE_SHEET_ID`
- `SV_API_KEY` is the random key you generated above

### Step 2.5: Deploy Modal App

```bash
modal deploy Executions/modal_sv_api.py
```

You should see output like:
```
✓ Created objects.
├── 🔨 Created function submit_job.
├── 🔨 Created function get_job_status.
├── 🔨 Created function get_job.
├── 🔨 Created function list_jobs.
├── 🔨 Created function health.
├── 🔨 Created function run_pipeline_worker.
└── 🔨 Created function handle_cors_preflight.

View app at https://modal.com/apps/ap-xxxxx

Deployed app sv-pipeline-api

Web endpoints:
├── submit_job      https://youruser--sv-pipeline-api-submit-job.modal.run
├── get_job_status  https://youruser--sv-pipeline-api-get-job-status.modal.run
├── get_job         https://youruser--sv-pipeline-api-get-job.modal.run
├── list_jobs       https://youruser--sv-pipeline-api-list-jobs.modal.run
├── health          https://youruser--sv-pipeline-api-health.modal.run
└── handle_cors...  https://youruser--sv-pipeline-api-handle-cors-preflight.modal.run
```

**Save these URLs** - you'll need the base URL for the frontend.

**Extract base URL**: If your endpoints are like:
- `https://youruser--sv-pipeline-api-submit-job.modal.run`
- `https://youruser--sv-pipeline-api-get-job-status.modal.run`

Then your base URL pattern is: `https://youruser--sv-pipeline-api-{function}.modal.run`

For the frontend, you'll use: `https://youruser--sv-pipeline-api` (without the function name)

### Step 2.6: Test Modal API

```bash
# Test health check
curl https://youruser--sv-pipeline-api-health.modal.run

# Should return: {"status": "healthy", "timestamp": "..."}

# Test job submission (replace YOUR_API_KEY with the one you generated)
curl -X POST https://youruser--sv-pipeline-api-submit-job.modal.run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://figured.com", "run_mode": "standard"}'

# Should return: {"job_id": "job_...", "status": "queued", "created_at": "..."}
```

If you get errors:
- Check Modal logs: `modal app logs sv-pipeline-api`
- Verify secrets are set correctly: `modal secret list`

---

## Phase 3: Generate Frontend with Lovable (2-3 hours)

### Step 3.1: Create Project in Lovable

1. Go to [lovable.dev](https://lovable.dev)
2. Start a new project
3. Upload the 4 UI inspiration PDFs from `ui inspiration/` folder

### Step 3.2: Prompt Lovable

Use this prompt (from `LOVABLE_INTEGRATION_GUIDE.md`):

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

[... rest of prompt from LOVABLE_INTEGRATION_GUIDE.md ...]

DESIGN SPECS:
- Color scheme: Green (#22C55E) for success, Yellow/Amber for warnings, Red for errors, Gray for neutral
- Card-based layout with rounded corners
- Clean white background
- Use Tailwind CSS
- Icons from lucide-react
- Responsive mobile-friendly design

FUNCTIONALITY:
- Form submission calls API
- Real-time polling for job status (every 3 seconds)
- Status badges with icons
- External link indicators for Google Docs/Sheets
```

### Step 3.3: Iterate on Design

- Refine the UI to match your inspiration PDFs
- Test the flow: Home → Submit → Job Detail → Dashboard
- Ensure all pages are created

### Step 3.4: Export Project

1. Click "Export" or "Download" in Lovable
2. Save the ZIP file
3. Extract it to a folder called `frontend/`

---

## Phase 4: Integrate Frontend with Backend (1 hour)

### Step 4.1: Copy API Proxy Routes

```bash
# Navigate to your exported Lovable project
cd frontend/

# Create API routes directory
mkdir -p app/api/jobs/{submit,[id],list}

# Copy proxy routes
cp ../frontend_api_routes/submit.ts app/api/jobs/submit/route.ts
cp ../frontend_api_routes/[id]/route.ts app/api/jobs/[id]/route.ts
cp ../frontend_api_routes/[id]/status/route.ts app/api/jobs/[id]/status/route.ts
cp ../frontend_api_routes/list/route.ts app/api/jobs/list/route.ts

# Copy API client
cp ../frontend_api_routes/client-api.ts lib/api.ts
```

### Step 4.2: Install Dependencies

```bash
npm install
npm install @tanstack/react-query
```

### Step 4.3: Create Polling Hooks

Create `hooks/useJob.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api, Job } from '@/lib/api';

export function useJob(jobId: string | null) {
  return useQuery<Job>({
    queryKey: ['job', jobId],
    queryFn: () => jobId ? api.getJobStatus(jobId) : Promise.reject(),
    enabled: !!jobId,
    refetchInterval: (data) => {
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
    refetchInterval: 10000  // Refresh every 10 seconds
  });
}
```

### Step 4.4: Update Lovable Components

Find where Lovable generated form submission and update to use the API client (see `LOVABLE_INTEGRATION_GUIDE.md` for detailed examples).

### Step 4.5: Create Environment Variables

Create `.env.local` in frontend/:

```bash
# Server-side only (NEVER use NEXT_PUBLIC_ for secrets)
MODAL_API_URL=https://youruser--sv-pipeline-api.modal.run
MODAL_API_KEY=your-api-key-here
```

Replace:
- `youruser--sv-pipeline-api` with your actual Modal app URL
- `your-api-key-here` with the API key you generated earlier

### Step 4.6: Test Locally

```bash
npm run dev
```

Open `http://localhost:3000` and test:
- Submit a job
- Check if it redirects to job detail page
- Verify polling updates every 3 seconds
- Check browser console for errors

---

## Phase 5: Deploy Frontend to Vercel (30 minutes)

### Step 5.1: Push to GitHub (if not already)

```bash
git init
git add .
git commit -m "Initial SV Analyzer frontend"
git branch -M main
git remote add origin your-repo-url
git push -u origin main
```

### Step 5.2: Deploy to Vercel

Option A: Via Vercel CLI

```bash
npm install -g vercel
vercel
```

Option B: Via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure build settings (Next.js should auto-detect)
5. Add environment variables:
   - `MODAL_API_URL` = `https://youruser--sv-pipeline-api.modal.run`
   - `MODAL_API_KEY` = `your-api-key-here`
6. Deploy

### Step 5.3: Test Production Deployment

1. Visit your Vercel URL (e.g., `https://sv-analyzer.vercel.app`)
2. Submit a test job
3. Verify it works end-to-end
4. Check Vercel logs if errors occur

---

## Phase 6: Update CORS in Modal (5 minutes)

Now that you have your Vercel domain, update CORS settings:

Edit `../Executions/modal_sv_api.py`:

```python
def add_cors_headers(response_dict: dict, status: int = 200):
    """Add CORS headers to response."""
    return {
        "body": response_dict,
        "status": status,
        "headers": {
            # ✅ Update this to your Vercel domain
            "Access-Control-Allow-Origin": "https://sv-analyzer.vercel.app",
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

## Phase 7: Final Testing (30 minutes)

### Test Checklist

- [ ] **Health check**: Visit Modal health endpoint, should return 200
- [ ] **Job submission**: Submit job via Vercel frontend
- [ ] **Real-time updates**: Progress bar updates every 3 seconds
- [ ] **Job completion**: Final results show scores, doc link, sheet link
- [ ] **Google Doc created**: Click "Open Profile Doc" link, verify doc exists
- [ ] **Google Sheet updated**: Click "Open in Sheets", verify row added
- [ ] **Jobs Sheet**: Check "Jobs" tab exists with job history
- [ ] **Dashboard**: All jobs show in dashboard table
- [ ] **Search/filter**: Dashboard search and filters work
- [ ] **Failed jobs**: Submit invalid URL, check error handling
- [ ] **Canadian research**: Submit job with "Deep Canada" mode
- [ ] **Multiple concurrent jobs**: Submit 3 jobs at once, all complete

### Verify Security

- [ ] **API key not exposed**: Open browser DevTools → Network tab, check requests to `/api/jobs/*`, should NOT see `SV_API_KEY` in headers
- [ ] **API key not in bundle**: Open DevTools → Sources tab, search for your API key, should find NOTHING
- [ ] **Modal endpoints auth**: Try calling Modal endpoint directly without Authorization header, should get 401

---

## Troubleshooting

### Problem: "Module 'google_auth_cloud' not found"

**Fix**: The import path needs to be absolute. Update imports in Modal:

```python
# In modal_sv_api.py, ensure code is mounted:
code_mount = modal.Mount.from_local_dir(".", remote_path="/root/sv_workflow")

# In background worker:
import sys
sys.path.insert(0, "/root/sv_workflow")
from Executions.google_auth_cloud import get_google_credentials
```

### Problem: "Failed to write to Jobs sheet"

**Fix**: Ensure service account has Editor access to the spreadsheet.

### Problem: CORS errors in browser

**Fix**:
1. Check `Access-Control-Allow-Origin` matches your Vercel domain
2. Redeploy Modal after changing CORS
3. Clear browser cache

### Problem: Jobs stuck in "queued" status

**Fix**:
1. Check Modal logs: `modal app logs sv-pipeline-api`
2. Look for errors in `run_pipeline_worker` function
3. Verify all secrets are set correctly

### Problem: Google authentication fails

**Fix**:
1. Verify `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` is complete JSON
2. Check service account email has access to Sheet and Drive
3. Test locally first with `python Executions/google_auth_cloud.py`

---

## Post-Deployment

### Monitor Usage

```bash
# View Modal logs
modal app logs sv-pipeline-api --follow

# Check job history in Google Sheets
# Open Master Prospect List → Jobs tab
```

### Cost Monitoring

Track costs in:
- **OpenAI**: https://platform.openai.com/usage
- **Firecrawl**: Your Firecrawl dashboard
- **Modal**: https://modal.com/usage
- **Vercel**: https://vercel.com/usage (should be $0 on free tier)

---

## Summary

You now have:

✅ **Backend**: Modal serverless API with async job execution
✅ **Frontend**: Next.js app on Vercel with real-time polling
✅ **Security**: API keys hidden server-side, never exposed to client
✅ **Storage**: Google Sheets for permanent history + Modal Dict for live state
✅ **Authentication**: Service account for cloud-compatible Google API access

**Total setup time: ~5-6 hours**

**Next steps:**
- Add team members to Vercel project
- Set up monitoring/alerts
- Customize UI branding
- Add more analysis modes

🎉 **Congratulations! Your SV Pipeline is live!**
