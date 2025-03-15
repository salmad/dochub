const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function processDocument(file: File, token: string) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/documents/process`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to process document');
  }

  return response.json();
}

export async function getDocuments(token: string) {
  const response = await fetch(`${API_URL}/documents`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }

  return response.json();
}

export async function searchDocuments(query: string, token: string) {
  const response = await fetch(`${API_URL}/documents/search?query=${encodeURIComponent(query)}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to search documents');
  }

  return response.json();
} 