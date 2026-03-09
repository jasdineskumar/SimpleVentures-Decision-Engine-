// frontend/app/api/jobs/list/route.ts
// List all jobs with pagination

import { NextRequest, NextResponse } from 'next/server';

const MODAL_API_URL = process.env.MODAL_API_URL;
const MODAL_API_KEY = process.env.MODAL_API_KEY;

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = searchParams.get('limit') || '50';
    const offset = searchParams.get('offset') || '0';

    // Forward to Modal with server-side API key
    const response = await fetch(
      `${MODAL_API_URL}/list_jobs?limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Authorization': `Bearer ${MODAL_API_KEY}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Failed to fetch jobs' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('List jobs error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
