import axios from "axios";

const TOKEN_KEY = "chatbot_auth_token";
const USER_KEY = "chatbot_auth_user";

const resolvedBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8000");

export const loadStoredToken = () => window.localStorage.getItem(TOKEN_KEY) || "";

export const persistAuth = (token, user) => {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const clearAuth = () => {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
};

const api = axios.create({
  baseURL: resolvedBaseUrl,
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = loadStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const register = async (email, password) => {
  const { data } = await api.post("/api/auth/register", { email, password });
  return data;
};

export const login = async (email, password) => {
  const { data } = await api.post("/api/auth/login", { email, password });
  return data;
};

export const fetchMe = async () => {
  const { data } = await api.get("/api/auth/me");
  return data;
};

export const fetchUsers = async () => {
  const { data } = await api.get("/api/auth/admin/users");
  return data;
};

export const updateUserRole = async (userId, isAdmin) => {
  const { data } = await api.patch(`/api/auth/admin/users/${userId}`, { is_admin: isAdmin });
  return data;
};

export const fetchKnowledgeStatus = async () => {
  const { data } = await api.get("/api/knowledge/status");
  return data;
};

export const fetchKnowledgeFiles = async () => {
  const { data } = await api.get("/api/knowledge/files");
  return data;
};

export const rebuildKnowledgeBase = async () => {
  const { data } = await api.post("/api/knowledge/rebuild");
  return data;
};

export const askQuestion = async (question, sessionId) => {
  const { data } = await api.post("/api/chat/ask", {
    question,
    session_id: sessionId,
  });
  return data;
};

export const createSession = async () => {
  const { data } = await api.post("/api/chat/sessions");
  return data;
};

export const fetchSessions = async () => {
  const { data } = await api.get("/api/chat/sessions");
  return data;
};

export const fetchSessionMessages = async (sessionId) => {
  const { data } = await api.get(`/api/chat/sessions/${sessionId}`);
  return data;
};

export const renameSession = async (sessionId, title) => {
  const { data } = await api.patch(`/api/chat/sessions/${sessionId}`, { title });
  return data;
};

export const deleteSession = async (sessionId) => {
  const { data } = await api.delete(`/api/chat/sessions/${sessionId}`);
  return data;
};
