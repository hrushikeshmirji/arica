import React from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Authentication requirement temporarily disabled: allow direct access to all features
  return <>{children}</>
}
