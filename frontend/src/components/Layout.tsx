import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import AlertBanner from './AlertBanner'
import PageProgressBar from './PageProgressBar'
import RealtimeStatusBadge from './RealtimeStatusBadge'
import { useHealth } from '../hooks/useHealth'
import {
  useOperationsOverview,
  useOperationsRealtime,
} from '../hooks/useOperations'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { connectionState: realtimeState, retryAttempt: realtimeRetryAttempt } =
    useOperationsRealtime()
  const { data: health, isLoading, isError } = useHealth()
  const { data: overview } = useOperationsOverview()
  const systemStatus = isError ? 'API offline' : isLoading ? 'Checking API' : 'API healthy'
  const statusTone = isError ? 'bg-lazarus-critical' : 'bg-lazarus-normal'

  return (
    <div className="min-h-screen bg-lazarus-bg">
      <PageProgressBar />
      <header className="sticky top-0 z-40 px-4 pt-0 sm:px-6">
        <div className="header-shell mx-auto max-w-[84rem] backdrop-blur-xl">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,0.9fr)_auto] xl:items-center">
            <Link to="/" className="group flex min-w-0 items-center gap-3.5">
              <div className="brand-mark flex h-12 w-12 shrink-0 items-center justify-center rounded-[1.35rem] border border-lazarus-border/70 transition-shadow duration-200 group-hover:shadow-md">
                <span className="font-display text-xs font-bold uppercase tracking-[0.22em] text-lazarus-text">
                  ICU
                </span>
              </div>
              <div className="min-w-0">
                <p className="display-kicker">Hospital digital twin</p>
                <h1 className="font-display text-[1.75rem] font-bold leading-none tracking-[-0.05em] text-lazarus-text">
                  St. Jude ICU
                </h1>
                <p className="mt-1 text-[11px] uppercase tracking-[0.19em] text-lazarus-muted/72">
                  Command center and live crisis simulation
                </p>
              </div>
            </Link>

            <div className="header-plaque hidden xl:block">
              <p className="text-sm font-semibold tracking-[-0.01em] text-lazarus-text/86">
                St. Jude&apos;s Research Hospital
              </p>
              <p className="mt-2 text-[11px] uppercase tracking-[0.28em] text-lazarus-muted/68">
                Critical care logistics and ward allocation twin
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-start gap-2.5 xl:justify-end">
              {overview && (
                <>
                  <span className="utility-chip">
                    Occupancy {overview.summary.icu_occupied}/{overview.summary.icu_capacity}
                  </span>
                  <span className="utility-chip hidden sm:inline-flex">
                    Overflow {overview.summary.overflow_patients}
                  </span>
                  <span className="utility-chip hidden sm:inline-flex">
                    Alerts {overview.summary.active_alerts}
                  </span>
                </>
              )}

              <RealtimeStatusBadge
                state={realtimeState}
                retryAttempt={realtimeRetryAttempt}
                compact
              />

              <div className="utility-chip normal-case tracking-[0.08em]">
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${statusTone} ${isError ? '' : 'motion-dot-live'}`}
                  aria-hidden="true"
                />
                <span>{systemStatus}</span>
                {health?.version && (
                  <span className="font-mono text-[10px] text-lazarus-muted/72">v{health.version}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <AlertBanner />

      <main className="mx-auto max-w-[84rem] px-4 py-8 sm:px-6 lg:py-10">
        {children}
      </main>
    </div>
  )
}
