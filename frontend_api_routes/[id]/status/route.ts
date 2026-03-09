// frontend/app/api/jobs/[id]/status/route.ts
// Get job status for polling

import { NextRequest, NextResponse } from 'next/server';

const MODAL_API_URL = process.env.MODAL_API_URL;
const MODAL_API_KEY = process.env.MODAL_API_KEY;

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const jobId = params.id;

    // Forward to Modal with server-side API key
    const response = await fetch(
      `${MODAL_API_URL}/get_job_status?job_id=${jobId}`,
      {
        headers: {
          'Authorization': `Bearer ${MODAL_API_KEY}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Failed to fetch job status' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Get job status error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
