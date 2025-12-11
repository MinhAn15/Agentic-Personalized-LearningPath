"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("token");
        const userData = localStorage.getItem("user");
        
        if (token && userData) {
          setUser(JSON.parse(userData));
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // For demo purposes, simulate successful login
      // In production, call: const data = await apiClient.signin(email, password);
      
      const mockUser: User = {
        id: email,
        name: email.split("@")[0],
        email: email,
      };

      // Store in localStorage
      localStorage.setItem("token", "demo_token_" + Date.now());
      localStorage.setItem("user", JSON.stringify(mockUser));
      
      setUser(mockUser);
      router.push("/dashboard");
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    setIsLoading(true);
    try {
      // Create learner profile in backend
      await apiClient.createLearnerProfile({
        learner_id: email,
        name: name,
        goal: "General learning",
        preferred_learning_style: "VISUAL",
      });

      const newUser: User = {
        id: email,
        name: name,
        email: email,
      };

      localStorage.setItem("token", "demo_token_" + Date.now());
      localStorage.setItem("user", JSON.stringify(newUser));
      
      setUser(newUser);
      router.push("/dashboard");
    } catch (error) {
      console.error("Signup failed:", error);
      // For demo, still create local user even if API fails
      const newUser: User = {
        id: email,
        name: name,
        email: email,
      };

      localStorage.setItem("token", "demo_token_" + Date.now());
      localStorage.setItem("user", JSON.stringify(newUser));
      
      setUser(newUser);
      router.push("/dashboard");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    router.push("/");
  };

  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        isAuthenticated: !!user, 
        isLoading, 
        login, 
        signup, 
        logout,
        setUser 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
