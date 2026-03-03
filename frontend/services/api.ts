import axios from "axios";

function resolveBackendBaseUrl() {
  const raw = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();
  const isProduction = process.env.NODE_ENV === "production";

  if (!raw) {
    if (typeof window !== "undefined") {
      const hostname = window.location.hostname;
      const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";

      if (!isLocalHost && isProduction) {
        return "/api";
      }
    }

    return "http://localhost:8080/api";
  }

  let trimmed = raw.replace(/\/+$/, "");

  if (trimmed.startsWith("/")) {
    return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
  }

  if (trimmed.startsWith(":")) {
    trimmed = `http://localhost${trimmed}`;
  } else if (/^localhost:\d+/i.test(trimmed)) {
    trimmed = `http://${trimmed}`;
  } else if (!/^https?:\/\//i.test(trimmed)) {
    trimmed = `${isProduction ? "https" : "http"}://${trimmed}`;
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
    const shouldHandleExpiredSession = status === 403 && message === "Invalid token";

    if (typeof window !== "undefined" && shouldHandleExpiredSession) {
      localStorage.removeItem("resume-analyzer-token");

      if (error?.response?.data && typeof error.response.data === "object") {
        error.response.data.message = "Session expired. Please login again.";
      }

      if (error?.response) {
        error.response.status = 401;
      }
    }

    return Promise.reject(error);
  }
);
