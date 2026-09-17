// Central backend URL.
//
// Set VITE_API_URL in frontend/.env (or in your host's environment variables)
// to point the app at a deployed backend. Falls back to the local dev server.
export const API_BASE_URL: string = import.meta.env.VITE_API_URL || "http://localhost:8000";
