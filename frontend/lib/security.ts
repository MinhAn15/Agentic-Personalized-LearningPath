import { useCallback, useRef } from "react";

// Input validation utilities
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function validatePassword(password: string): { valid: boolean; message: string } {
  if (password.length < 8) {
    return { valid: false, message: "Password must be at least 8 characters" };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: "Password must contain at least one uppercase letter" };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: "Password must contain at least one lowercase letter" };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: "Password must contain at least one number" };
  }
  return { valid: true, message: "" };
}

export function validateName(name: string): boolean {
  return name.trim().length >= 2 && name.trim().length <= 100;
}

// XSS protection - sanitize user input
export function sanitizeInput(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;")
    .replace(/\//g, "&#x2F;");
}

// Rate limiting hook
export function useRateLimit(maxRequests: number = 10, windowMs: number = 60000) {
  const requestLog = useRef<number[]>([]);

  const checkLimit = useCallback((): boolean => {
    const now = Date.now();
    const log = requestLog.current;
    
    // Remove old requests outside the window
    while (log.length > 0 && log[0] < now - windowMs) {
      log.shift();
    }

    // Check if limit exceeded
    if (log.length >= maxRequests) {
      return false;
    }

    // Log this request
    log.push(now);
    return true;
  }, [maxRequests, windowMs]);

  return { checkLimit };
}

// CSRF token management
export function generateCSRFToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function storeCSRFToken(token: string): void {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("csrf_token", token);
  }
}

export function getCSRFToken(): string | null {
  if (typeof window !== "undefined") {
    return sessionStorage.getItem("csrf_token");
  }
  return null;
}

// Secure storage wrapper
export const secureStorage = {
  set(key: string, value: string): void {
    if (typeof window !== "undefined") {
      try {
        // In production, consider encrypting sensitive data
        localStorage.setItem(key, value);
      } catch (e) {
        console.error("Storage error:", e);
      }
    }
  },

  get(key: string): string | null {
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem(key);
      } catch (e) {
        console.error("Storage error:", e);
        return null;
      }
    }
    return null;
  },

  remove(key: string): void {
    if (typeof window !== "undefined") {
      try {
        localStorage.removeItem(key);
      } catch (e) {
        console.error("Storage error:", e);
      }
    }
  },

  clear(): void {
    if (typeof window !== "undefined") {
      try {
        localStorage.clear();
      } catch (e) {
        console.error("Storage error:", e);
      }
    }
  },
};

// Content Security Policy headers (for reference)
export const CSP_HEADERS = {
  "Content-Security-Policy": [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' http://localhost:8000 https://api.yourapp.com",
    "frame-ancestors 'none'",
  ].join("; "),
};
