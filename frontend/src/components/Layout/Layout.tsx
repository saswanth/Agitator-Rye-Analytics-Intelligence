import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Executive Dashboard', subtitle: 'Real-time KPIs & business overview' },
  '/bi': { title: 'Conversational BI', subtitle: 'Ask questions in plain English' },
  '/rca': { title: 'Root Cause Analysis', subtitle: 'Automated anomaly investigation' },
  '/financial': { title: 'Financial Analysis', subtitle: 'P&L, forecasting & scenario modeling' },
  '/pipeline': { title: 'Data Pipeline', subtitle: 'Quality monitoring & ETL management' },
  '/insights': { title: 'Auto Insights', subtitle: 'AI-generated narrative intelligence' },
}

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const pageInfo = PAGE_TITLES[location.pathname] ?? { title: 'Agitator Rye', subtitle: '' }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-navy-900 bg-grid">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
