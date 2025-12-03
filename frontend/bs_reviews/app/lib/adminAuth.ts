// lib/adminAuth.ts
// Utility functions for admin authentication

export const getAdminToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("adminToken");
};

export const getAdminEmail = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("adminEmail");
};

export const isAdminAuthenticated = (): boolean => {
  const token = getAdminToken();
  const email = getAdminEmail();
  return !!(token && email);
};

export const clearAdminAuth = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("adminToken");
  localStorage.removeItem("adminEmail");
};

export const setAdminAuth = (token: string, email: string): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem("adminToken", token);
  localStorage.setItem("adminEmail", email);
};

// Helper to make authenticated API requests
export const adminFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAdminToken();

  if (!token) {
    throw new Error("No admin token found");
  }

  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  return fetch(url, {
    ...options,
    headers,
  });
};
