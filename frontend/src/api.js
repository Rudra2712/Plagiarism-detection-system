// src/api.js
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Optional: log errors globally (useful in dev)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("API Error:", err?.response?.data || err.message);
    return Promise.reject(err);
  }
);
export const uploadFiles = (formData) =>
  api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const runCheck = () => api.post("/api/check");

export const cleanup = () => api.post("/api/cleanup");

export default api;
