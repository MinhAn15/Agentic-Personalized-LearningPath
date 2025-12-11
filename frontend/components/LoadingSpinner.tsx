"use client";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  fullScreen?: boolean;
}

export default function LoadingSpinner({ 
  size = "md", 
  text = "Loading...",
  fullScreen = false 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "w-6 h-6 border-2",
    md: "w-10 h-10 border-3",
    lg: "w-16 h-16 border-4",
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizeClasses[size]} border-blue-600 border-t-transparent rounded-full animate-spin`}
      />
      {text && (
        <p className="text-slate-600 dark:text-slate-400 text-sm animate-pulse">
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

// Skeleton loader for cards
export function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 animate-pulse">
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4 mb-4"></div>
      <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2 mb-2"></div>
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
    </div>
  );
}

// Skeleton loader for list items
export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 animate-pulse"
        >
          <div className="flex justify-between items-center mb-2">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-24"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-12"></div>
          </div>
          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
        </div>
      ))}
    </div>
  );
}

// Loading button state
export function LoadingButton({ 
  loading, 
  children, 
  className = "",
  ...props 
}: { 
  loading: boolean; 
  children: React.ReactNode;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`relative ${className} ${loading ? "cursor-not-allowed opacity-70" : ""}`}
      disabled={loading}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      <span className={loading ? "invisible" : ""}>{children}</span>
    </button>
  );
}
