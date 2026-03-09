// frontend/app/api/jobs/submit/route.ts
// Next.js 13+ App Router API route

import { NextRequest, NextResponse } from 'next/server';

const MODAL_API_URL = process.env.MODAL_API_URL; // Server-side only
const MODAL_API_KEY = process.env.MODAL_API_KEY; // Server-side only, NEVER expose

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate input
    if (!body.url) {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      );
    }

    // Forward to Modal with server-side API key
    const response = await fetch(`${MODAL_API_URL}/submit_job`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${MODAL_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: body.url,
        company_name: body.company_name || '',
        run_mode: body.run_mode || 'standard',
        notes: body.notes || '',
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Failed to submit job' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Submit job error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
