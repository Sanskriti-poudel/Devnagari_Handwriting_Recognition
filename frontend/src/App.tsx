import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { AppLayout } from '@/layouts/AppLayout'
import { AuthLayout } from '@/layouts/AuthLayout'
import { ProtectedRoute, GuestRoute } from '@/routes/ProtectedRoute'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { Loader } from '@/components/ui/Loader'

const LandingPage = lazy(() => import('@/pages/LandingPage'))
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const SignupPage = lazy(() => import('@/pages/SignupPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const OcrPage = lazy(() => import('@/pages/OcrPage'))
const HistoryPage = lazy(() => import('@/pages/HistoryPage'))
const ModelsPage = lazy(() => import('@/pages/ModelsPage'))
const ProfilePage = lazy(() => import('@/pages/ProfilePage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

function FullscreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-light text-violet-500 dark:bg-surface-dark">
      <Loader size={36} />
    </div>
  )
}

export default function App() {
  const location = useLocation()

  return (
    <ErrorBoundary>
      <Suspense fallback={<FullscreenLoader />}>
        <AnimatePresence mode="wait" initial={false}>
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<LandingPage />} />

            <Route element={<GuestRoute />}>
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/ocr" element={<OcrPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/models" element={<ModelsPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </ErrorBoundary>
  )
}
