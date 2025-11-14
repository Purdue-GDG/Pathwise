/**
 * Shared function to structure form data and send to backend
 */

export async function submitToBackend(formDataJson) {

  const structuredPrompt = {
    major: formDataJson.major || null,
    academicInterests: formDataJson.academicInterests || null,
    courseType: formDataJson.courseType || null,
    timestamp: new Date().toISOString(),
  };

  console.log('Structured prompt to send to backend:', JSON.stringify(structuredPrompt, null, 2));

  // Get backend URL
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000/api/prompt';
  
  try {
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(structuredPrompt),
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      throw new Error(`Backend responded with status ${backendResponse.status}: ${errorText}`);
    }

    const backendData = await backendResponse.json();

    return {
      success: true,
      message: 'Form data sent successfully to backend',
      data: backendData,
      prompt: structuredPrompt,
    };
  } catch (fetchError) {
    console.warn('Backend not available:', fetchError.message);
    console.warn('Structured prompt that would be sent:', JSON.stringify(structuredPrompt, null, 2));
    
    return {
      success: true,
      message: 'Form data structured successfully',
      prompt: structuredPrompt,
      warning: `Backend at ${backendUrl} is not reachable. Check your backend server.`,
    };
  }
}


