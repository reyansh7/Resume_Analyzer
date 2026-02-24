import axios from "axios";

function resolveBackendBaseUrl() {
  const raw = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080/api";
  const trimmed = raw.replace(/\/+$/, "");
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
}

export const api = axios.create({
  baseURL: resolveBackendBaseUrl(),
  timeout: 20000
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("resume-analyzer-token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
