'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

interface User {
  id: string
  email: string
  name: string
  learningStyle?: string
  goal?: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<boolean>
  signup: (data: SignupData) => Promise<boolean>
  logout: () => void
}

interface SignupData {
  name: string
  email: string
  password: string
  learningGoal?: string
  learningStyle?: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          setUser(JSON.parse(storedUser))
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true)
      
      // In production, authenticate with backend
      // For now, simulate login
      const userData: User = {
        id: email,
        email,
        name: email.split('@')[0],
      }

      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('learner_id', email)
      setUser(userData)
      
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (data: SignupData): Promise<boolean> => {
    try {
      setIsLoading(true)

      // Create profile with Profiler Agent
      const response = await api.createProfile({
        learner_id: data.email,
        name: data.name,
        goal: data.learningGoal || 'General learning',
        preferred_learning_style: data.learningStyle || 'VISUAL',
      })

      if (response.error) {
        throw new Error(response.error)
      }

      const userData: User = {
        id: data.email,
        email: data.email,
        name: data.name,
        learningStyle: data.learningStyle,
        goal: data.learningGoal,
      }

      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('learner_id', data.email)
      setUser(userData)

      return true
    } catch (error) {
      console.error('Signup failed:', error)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('learner_id')
    localStorage.removeItem('auth_token')
    setUser(null)
    router.push('/')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
