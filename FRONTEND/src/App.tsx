import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeProvider'
import { LanguageProvider } from './contexts/LanguageContext'
import { AuthProvider } from './contexts/AuthContext'
import { ScanHistoryProvider } from './contexts/ScanHistoryContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { PlantationProvider } from './contexts/PlantationContext'
import { WeatherProvider } from './contexts/WeatherContext'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

// Route-level code-splitting: each page loads as a separate chunk
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Detection = lazy(() => import('./pages/Detection'))
const Diseases = lazy(() => import('./pages/Diseases'))
const Analytics = lazy(() => import('./pages/Analytics'))
const PlantationMap = lazy(() => import('./pages/PlantationMap'))
const Weather = lazy(() => import('./pages/Weather'))
const RiskForecast = lazy(() => import('./pages/RiskForecast'))
const ScanHistory = lazy(() => import('./pages/ScanHistory'))
const Reports = lazy(() => import('./pages/Reports'))
const Research = lazy(() => import('./pages/Research'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Settings = lazy(() => import('./pages/Settings'))
const AIAssistant = lazy(() => import('./pages/AIAssistant'))
const Admin = lazy(() => import('./pages/Admin'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes default
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function AppLayout({ children }: { children: React.ReactNode }) {
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider defaultTheme="system" storageKey="arecavision-theme">
          <LanguageProvider>
            <AuthProvider>
              <NotificationProvider>
                <PlantationProvider>
                  <WeatherProvider>
                  <ScanHistoryProvider>
                    <BrowserRouter>
                      <Suspense
                        fallback={
                          <div className="flex h-screen w-screen items-center justify-center bg-background text-foreground transition-colors">
                            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                          </div>
                        }
                      >
                        <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
                        <Route
                          path="/dashboard"
                          element={<ProtectedRoute><AppLayout><Dashboard /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/detection"
                          element={<AppLayout><Detection /></AppLayout>}
                        />
                        <Route
                          path="/diseases"
                          element={<AppLayout><Diseases /></AppLayout>}
                        />
                        <Route
                          path="/analytics"
                          element={<ProtectedRoute><AppLayout><Analytics /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/map"
                          element={<ProtectedRoute><AppLayout><PlantationMap /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/weather"
                          element={<ProtectedRoute><AppLayout><Weather /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/risk"
                          element={<ProtectedRoute><AppLayout><RiskForecast /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/scans"
                          element={<ProtectedRoute><AppLayout><ScanHistory /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/reports"
                          element={<ProtectedRoute><AppLayout><Reports /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/assistant"
                          element={<ProtectedRoute><AppLayout><AIAssistant /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/research"
                          element={<ProtectedRoute><AppLayout><Research /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/admin"
                          element={<ProtectedRoute requireAdmin><AppLayout><Admin /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/notifications"
                          element={<ProtectedRoute><AppLayout><Notifications /></AppLayout></ProtectedRoute>}
                        />
                        <Route
                          path="/settings"
                          element={<ProtectedRoute><AppLayout><Settings /></AppLayout></ProtectedRoute>}
                        />
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                      </Suspense>
                    </BrowserRouter>
                  </ScanHistoryProvider>
                  </WeatherProvider>
                </PlantationProvider>
              </NotificationProvider>
            </AuthProvider>
          </LanguageProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

