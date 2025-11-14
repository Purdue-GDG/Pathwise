import { NextResponse } from 'next/server';
import { submitToBackend } from './submitToBackend';

/**
 * API Route: /api/submit
 * This creates a structured prompt JSON and forwards it to the backend API.
 */
export async function POST(request) {
  try {
    const body = await request.json();
    
    const result = await submitToBackend(body);
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error processing form data:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to process form data',
      },
      { status: 500 }
    );
  }
}

