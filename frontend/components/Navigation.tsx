"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navigation() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path ? "text-blue-600" : "text-slate-600";

  return (
    <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg"></div>
            <span className="font-bold text-lg">PathAI</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex gap-8">
            <Link href="/" className={`${isActive("/")} hover:text-slate-900 transition`}>
              Home
            </Link>
            <Link href="#features" className="text-slate-600 hover:text-slate-900 transition">
              Features
            </Link>
            <Link href="#" className="text-slate-600 hover:text-slate-900 transition">
              About
            </Link>
          </div>

          {/* Auth Buttons */}
          <div className="flex gap-4">
            <Link
              href="/auth/signin"
              className="px-4 py-2 text-slate-600 hover:text-slate-900 transition"
            >
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
