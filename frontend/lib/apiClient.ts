const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FetchResponse<T> {
  data: T | null;
  error: string | null;
}

/**
 * A standardized fetch wrapper that ensures the UI never crashes due to network errors.
 * Automatically prepends the base URL, handles JSON parsing, and catches timeouts.
 */
export async function fetchWrapper<T = any>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 8000
): Promise<FetchResponse<T>> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  // Allow absolute URLs to bypass the BASE_URL logic if needed
  const url = endpoint.startsWith('http') 
    ? endpoint 
    : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: controller.signal,
    });
    
    clearTimeout(id);

    if (!response.ok) {
      // Return a clean error without throwing an exception to the UI
      return { 
        data: null, 
        error: `API Error: ${response.status} ${response.statusText}` 
      };
    }

    const data = await response.json();
    return { data, error: null };
    
  } catch (err: any) {
    clearTimeout(id);
    
    let errorMessage = "An unexpected network error occurred.";
    if (err.name === 'AbortError') {
      errorMessage = "Network request timed out.";
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    return { data: null, error: errorMessage };
  }
}
