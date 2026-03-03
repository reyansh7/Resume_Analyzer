import axios from "axios";

function resolveBackendBaseUrl() {
  const raw = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080/api";
  let trimmed = raw.trim().replace(/\/+$/, "");

  if (trimmed.startsWith(":")) {
    trimmed = `http://localhost${trimmed}`;
  } else if (/^localhost:\d+/i.test(trimmed)) {
    trimmed = `http://${trimmed}`;
  } else if (!/^https?:\/\//i.test(trimmed)) {
    trimmed = `http://${trimmed}`;
  }

  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
}

export const api = axios.create({
  baseURL: resolveBackendBaseUrl(),
  timeout: 120000,
  withCredentials: true
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

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status as number | undefined;
    const message = error?.response?.data?.message as string | undefined;
    const originalRequest = error?.config as (typeof error.config & { _retriedWithoutAuth?: boolean }) | undefined;
    const shouldRetryWithCookieFallback = status === 403 && message === "Invalid token";

    if (
      typeof window !== "undefined" &&
      shouldRetryWithCookieFallback &&
      originalRequest &&
      !originalRequest._retriedWithoutAuth
    ) {
      localStorage.removeItem("resume-analyzer-token");
      originalRequest._retriedWithoutAuth = true;

      if (originalRequest.headers && "Authorization" in originalRequest.headers) {
        delete originalRequest.headers.Authorization;
      }

      return api.request(originalRequest);
    }

    return Promise.reject(error);
  }
);
