"use client";

import { Component, ReactNode } from "react";
import Link from "next/link";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    
    // TODO: Send to error tracking service (Sentry, etc.)
    // if (typeof window !== "undefined" && window.Sentry) {
    //   window.Sentry.captureException(error);
    // }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
          <div className="max-w-md w-full bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8 text-center">
            <div className="text-6xl mb-4">😕</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Oops! Something went wrong
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              We&apos;re sorry, but something unexpected happened. Please try again.
            </p>
            
            {process.env.NODE_ENV === "development" && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm text-slate-500 dark:text-slate-400 mb-2">
                  Error details (dev only)
                </summary>
                <pre className="text-xs bg-slate-100 dark:bg-slate-700 p-3 rounded overflow-auto max-h-40">
                  {this.state.error.message}
                  {"\n\n"}
                  {this.state.error.stack}
                </pre>
              </details>
            )}

            <div className="flex gap-4 justify-center">
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
              >
                Try Again
              </button>
              <Link
                href="/"
                className="px-6 py-2 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition text-slate-700 dark:text-slate-300"
              >
                Go Home
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Error message component for inline errors
export function ErrorMessage({ 
  message, 
  onRetry 
}: { 
  message: string; 
  onRetry?: () => void;
}) {
  return (
    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-xl">⚠️</span>
        <div className="flex-1">
          <p className="text-red-700 dark:text-red-400">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
            >
              Click to retry →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Empty state component
export function EmptyState({ 
  icon = "📭",
  title = "No data found",
  description = "There&apos;s nothing here yet.",
  action,
}: {
  icon?: string;
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-slate-600 dark:text-slate-400 mb-6">
        {description}
      </p>
      {action}
    </div>
  );
}
