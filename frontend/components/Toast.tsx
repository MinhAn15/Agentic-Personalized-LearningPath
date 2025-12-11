"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback((type: ToastType, message: string, duration = 5000) => {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { id, type, message, duration };

    setToasts((prev) => [...prev, newToast]);

    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
      }, duration);
    }
  }, []);

  const success = useCallback((message: string) => addToast("success", message), [addToast]);
  const error = useCallback((message: string) => addToast("error", message), [addToast]);
  const info = useCallback((message: string) => addToast("info", message), [addToast]);
  const warning = useCallback((message: string) => addToast("warning", message), [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, info, warning }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

// Toast Container
function ToastContainer({ 
  toasts, 
  removeToast 
}: { 
  toasts: Toast[]; 
  removeToast: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

// Individual Toast
function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const typeStyles = {
    success: "bg-green-50 dark:bg-green-900/90 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200",
    error: "bg-red-50 dark:bg-red-900/90 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200",
    info: "bg-blue-50 dark:bg-blue-900/90 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200",
    warning: "bg-yellow-50 dark:bg-yellow-900/90 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200",
  };

  const icons = {
    success: "✅",
    error: "❌",
    info: "ℹ️",
    warning: "⚠️",
  };

  return (
    <div
      className={`${typeStyles[toast.type]} border rounded-lg p-4 shadow-lg flex items-start gap-3 animate-slide-up`}
      role="alert"
    >
      <span className="text-lg flex-shrink-0">{icons[toast.type]}</span>
      <p className="flex-1 text-sm">{toast.message}</p>
      <button
        onClick={onClose}
        className="text-current opacity-50 hover:opacity-100 transition"
        aria-label="Close"
      >
        ✕
      </button>
    </div>
  );
}

// Standalone toast component (for non-context usage)
export function Toast({ 
  type, 
  message, 
  onClose 
}: { 
  type: ToastType; 
  message: string; 
  onClose: () => void;
}) {
  return <ToastItem toast={{ id: "standalone", type, message }} onClose={onClose} />;
}
