// Health check API route for Vercel/frontend monitoring
import { NextResponse } from 'next/server';

export async function GET() {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'frontend',
    version: '1.0.0',
    checks: {
      api: await checkBackendHealth(),
    },
  };

  const statusCode = health.checks.api ? 200 : 503;
  
  return NextResponse.json(health, { status: statusCode });
}

async function checkBackendHealth(): Promise<boolean> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      cache: 'no-store',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
