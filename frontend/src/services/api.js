const BACKEND_URL_KEY = "mnn_backend_url";
const ACCESS_TOKEN_KEY = "mnn_access_token";

const stripTrailingSlash = (value) => value.replace(/\/+$/, "");

export const getBackendUrl = () => {
  const envValue = import.meta.env.VITE_BACKEND_URL || "";
  const savedValue = localStorage.getItem(BACKEND_URL_KEY) || envValue;
  return stripTrailingSlash(savedValue || "http://127.0.0.1:8000");
};

export const setBackendUrl = (url) => {
  localStorage.setItem(BACKEND_URL_KEY, stripTrailingSlash(url.trim()));
};

export const setAccessToken = (token) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
};

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY) || "";

export const clearSession = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
};

const request = async (path, options = {}) => {
  const token = getAccessToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${getBackendUrl()}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });

  const contentType = response.headers.get("Content-Type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const message = data?.detail || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
};

export const loginOperator = async (username, password) => {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setAccessToken(data.access_token);
  return data;
};

export const getProfile = async () => request("/auth/me");

export const getDashboardOverview = async () => request("/dashboard/overview");

export const runQuery = async (query) =>
  request("/query", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
