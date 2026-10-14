import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from "react"
import { UserTokenPayload, LoginRequest, RegisterRequest } from "../types/api"
import { loginUser, registerUser, logoutUser, getStoredUser, refreshUserSession } from "../services/authService"
import { onUnauthorized } from "../services/apiClient"

interface AuthContextType {
  user: UserTokenPayload | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
})

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserTokenPayload | null>(() => getStoredUser())
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const isMountedRef = useRef(true)

  useEffect(() => {
    isMountedRef.current = true
    // Session initialization check
    const initAuth = async () => {
      if (user) {
        try {
          const refreshed = await refreshUserSession()
          if (!isMountedRef.current) return
          if (refreshed) {
            setUser(refreshed.user)
          } else {
            setUser(null)
          }
        } catch {
          if (!isMountedRef.current) return
          setUser(null)
        }
      }
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }

    initAuth()

    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    // 401 Interceptor Listener
    const unsubscribe = onUnauthorized(() => {
      setUser(null)
    })
    return () => unsubscribe()
  }, [])

  const handleLogin = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      const authRes = await loginUser(credentials)
      setUser(authRes.user)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleRegister = useCallback(async (data: RegisterRequest) => {
    setIsLoading(true)
    try {
      const authRes = await registerUser(data)
      setUser(authRes.user)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleLogout = useCallback(async () => {
    setIsLoading(true)
    try {
      await logoutUser()
    } finally {
      setUser(null)
      setIsLoading(false)
    }
  }, [])

  const contextValue = useMemo(() => ({
    user,
    isAuthenticated: !!user,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  }), [user, isLoading, handleLogin, handleRegister, handleLogout])

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
