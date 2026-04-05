import axios from "axios";

const resolveApiBase = () => {
  const envBase = import.meta.env.VITE_API_BASE;
  if (envBase && envBase.trim().length > 0) {
    return envBase;
  }
  if (import.meta.env.MODE === "development") {
    return "http://localhost:8000";
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:8000";
};

export const api = axios.create({
  baseURL: resolveApiBase(),
  timeout: 120000,
});

// Request interceptor to inject the JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("AUTH_TOKEN");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
