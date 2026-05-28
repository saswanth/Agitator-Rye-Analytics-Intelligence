import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Executive Dashboard', subtitle: 'Real-time KPIs & business overview' },
  '/bi': { title: 'Conversational BI', subtitle: 'Ask questions in plain English' },
  '/rca': { title: 'Root Cause Analysis', subtitle: 'Automated anomaly investigation' },
  '/financial': { title: 'Financial Analysis', subtitle: 'P&L, forecasting & scenario modeling' },
  '/pipeline': { title: 'Data Pipeline', subtitle: 'Quality monitoring & ETL management' },
  '/insights': { title: 'Auto Insights', subtitle: 'AI-generated narrative intelligence' },
}

function AppLayout() {
  const location = useLocation()
  const pageInfo = PAGE_TITLES[location.pathname] ?? { title: 'Agitator Rye', subtitle: '' }
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-navy-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

const Home = lazy(() => import('./pages/Home'))
const BI = lazy(() => import('./pages/BI'))
const RootCause = lazy(() => import('./pages/RootCause'))
const Financial = lazy(() => import('./pages/Financial'))
const Pipeline = lazy(() => import('./pages/Pipeline'))
const Insights = lazy(() => import('./pages/Insights'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="w-10 h-10 border-2 border-cyan-glow/20 border-t-cyan-glow rounded-full animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Suspense fallback={<PageLoader />}><Home /></Suspense>} />
            <Route path="bi" element={<Suspense fallback={<PageLoader />}><BI /></Suspense>} />
            <Route path="rca" element={<Suspense fallback={<PageLoader />}><RootCause /></Suspense>} />
            <Route path="financial" element={<Suspense fallback={<PageLoader />}><Financial /></Suspense>} />
            <Route path="pipeline" element={<Suspense fallback={<PageLoader />}><Pipeline /></Suspense>} />
            <Route path="insights" element={<Suspense fallback={<PageLoader />}><Insights /></Suspense>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0D1525',
            color: '#E5E7EB',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#00C896', secondary: '#0D1525' } },
          error: { iconTheme: { primary: '#FF4757', secondary: '#0D1525' } },
        }}
      />
    </QueryClientProvider>
  )
}
