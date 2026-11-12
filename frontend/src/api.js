// Where the backend lives. Vite inlines VITE_API_BASE_URL at build time, so the
// value in effect is whatever was set when `npm run build` ran — changing it
// means rebuilding the frontend.
//
// Unset (the default) leaves paths relative, so `npm run dev` and
// `npm run preview` keep going through the Vite proxy to localhost:8001.
// For GitHub Pages, set it to the backend's origin, e.g.
// VITE_API_BASE_URL=https://<service>.onrender.com
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`
}
