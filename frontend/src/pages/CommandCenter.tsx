import { useState } from 'react'
import ICUBedHeatmap from '../components/ICUBedHeatmap'
import IncidentHandoffPanel from '../components/IncidentHandoffPanel'
import OperationsBriefingPanel from '../components/OperationsBriefingPanel'
import OperatorActivityPanel from '../components/OperatorActivityPanel'
import PatientFlowTimeline from '../components/PatientFlowTimeline'
import Reveal from '../components/Reveal'
import RecommendedActionsPanel from '../components/RecommendedActionsPanel'
import ResourceConsumptionPanel from '../components/ResourceConsumptionPanel'
import RoomAvailabilityPanel from '../components/RoomAvailabilityPanel'
import ScenarioComparisonPanel from '../components/ScenarioComparisonPanel'
import ScenarioPlaybooksPanel, {
  type ScenarioPlaybook,
} from '../components/ScenarioPlaybooksPanel'
import SimulationControlPanel from '../components/SimulationControlPanel'
import type {
  BedAvailabilityFilter,
  RecommendedAction,
} from '../types'
import {
  useOperationsOverview,
  useSimulationControl,
} from '../hooks/useOperations'

function toneForMetric(value: number, thresholds: [number, number]) {
  if (value >= thresholds[1]) {
    return 'text-lazarus-critical'
  }

  if (value >= thresholds[0]) {
    return 'text-lazarus-warning'
  }

  return 'text-lazarus-normal'
}

export default function CommandCenter() {
  const { data: overview, isLoading, error } = useOperationsOverview()
  const control = useSimulationControl()
  const [availabilityFilter, setAvailabilityFilter] =
    useState<BedAvailabilityFilter>('all')
  const [selectedZone, setSelectedZone] = useState<string | null>(null)

  async function runPlaybook(playbook: ScenarioPlaybook) {
    if (overview?.simulation.is_paused) {
      await control.mutateAsync({ action: 'resume' })
    }

    await control.mutateAsync({
      action: 'set_speed',
      speed: playbook.speed,
    })

    await control.mutateAsync({
      action: 'inject_crisis',
      scenario: playbook.scenario,
      severity: playbook.severity,
      patient_count: playbook.patientCount,
    })
  }

  function executeRecommendation(action: RecommendedAction) {
    if (action.action_type === 'intervention') {
      control.mutate({
        action: 'apply_intervention',
        intervention_id: action.id,
      })
      return
    }

    if (action.action_type === 'control' && action.control_action) {
      control.mutate({
        action: action.control_action,
      })
    }
  }

  if (isLoading) {
    return (
      <div className="card">
        <h2 className="text-lazarus-text font-semibold">Loading command center</h2>
        <p className="mt-2 text-sm text-lazarus-muted">
          Building the latest ICU twin snapshot, bed allocation, and resource forecast.
        </p>
      </div>
    )
  }

  if (error || !overview) {
    return (
      <div className="card border-lazarus-critical">
        <h2 className="text-lazarus-critical font-semibold mb-2">Command center unavailable</h2>
        <p className="text-lazarus-muted text-sm">
          The ICU operations snapshot could not be loaded. Check the backend and
          websocket services, then refresh the page.
        </p>
      </div>
    )
  }

  const { summary, simulation } = overview
  const activeInterventions = simulation.active_interventions ?? []

  return (
    <div className="page-entrance space-y-6">
      <Reveal
        as="section"
        className={`hero-panel ${
          summary.overflow_patients > 0 || summary.active_alerts > 0
            ? 'hero-panel-critical'
            : ''
        }`}
        delay={40}
      >
        <div className="relative z-10 grid gap-8 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] xl:items-end">
          <div className="max-w-3xl">
            <p className="display-kicker">Operational command dashboard</p>
            <h1 className="display-title headline-reveal mt-3">
              St. Jude ICU <span className="text-clinical-gradient">Digital Twin</span> for
              high-pressure logistics and live crisis response.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-lazarus-muted">
              This command surface simulates bed routing, tracks critical resource burn,
              and exposes patient-flow pressure as conditions shift across the ICU.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              <span className="dossier-chip">Scenario {simulation.crisis_label}</span>
              <span className="dossier-chip">Speed {simulation.speed.toFixed(1)}x</span>
              <span className="dossier-chip">Attention queue {summary.attention_patients}</span>
              <span className="dossier-chip">
                Last update{' '}
                {new Date(summary.updated_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
            {activeInterventions.length > 0 ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {activeInterventions.map((intervention) => (
                  <article
                    key={intervention.id}
                    className="rounded-[1.4rem] border border-lazarus-info/20 bg-lazarus-surface/78 p-4 shadow-[0_20px_45px_rgba(7,20,25,0.18)]"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="section-label">Active intervention</p>
                        <h2 className="mt-2 text-base font-semibold text-lazarus-text">
                          {intervention.label}
                        </h2>
                      </div>
                      <span className="rounded-full bg-lazarus-info/14 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-lazarus-info">
                        {intervention.value}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-lazarus-muted">
                      {intervention.effect}
                    </p>
                  </article>
                ))}
              </div>
            ) : null}
          </div>

          <div className="shell-frame grid grid-cols-2 gap-3">
            <div className="metric-frame">
              <p className="section-label">ICU occupied</p>
              <p className="metric-value">
                {summary.icu_occupied}/{summary.icu_capacity}
              </p>
            </div>
            <div className="metric-frame">
              <p className="section-label">Active alerts</p>
              <p className={`metric-value ${toneForMetric(summary.active_alerts, [1, 3])}`}>
                {summary.active_alerts}
              </p>
            </div>
            <div className="metric-frame">
              <p className="section-label">Overflow</p>
              <p className={`metric-value ${toneForMetric(summary.overflow_patients, [1, 3])}`}>
                {summary.overflow_patients}
              </p>
            </div>
            <div className="metric-frame">
              <p className="section-label">Average risk</p>
              <p
                className={`metric-value ${toneForMetric(summary.average_risk_score, [45, 70])}`}
              >
                {summary.average_risk_score}
              </p>
            </div>
          </div>
        </div>
      </Reveal>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Reveal delay={90}>
          <OperationsBriefingPanel
            briefing={overview.briefing}
            trust={overview.trust}
          />
        </Reveal>
        <Reveal delay={150}>
          <RecommendedActionsPanel
            actions={overview.recommended_actions}
            isPending={control.isPending}
            onExecuteAction={executeRecommendation}
          />
        </Reveal>
      </div>

      <Reveal delay={120}>
        <ScenarioComparisonPanel comparison={overview.scenario_comparison} />
      </Reveal>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(22rem,0.85fr)] xl:items-start">
        <div className="space-y-6">
          <RoomAvailabilityPanel
            beds={overview.bed_heatmap}
            triageQueue={overview.triage_queue}
            availabilityFilter={availabilityFilter}
            selectedZone={selectedZone}
            onAvailabilityFilterChange={setAvailabilityFilter}
            onZoneChange={setSelectedZone}
          />
          <ICUBedHeatmap
            beds={overview.bed_heatmap}
            triageQueue={overview.triage_queue}
            availabilityFilter={availabilityFilter}
            selectedZone={selectedZone}
          />
          <ResourceConsumptionPanel
            cards={overview.resource_cards}
            forecast={overview.resource_forecast}
          />
          <PatientFlowTimeline
            timeline={overview.timeline}
            replayFrames={overview.replay_frames}
          />
        </div>

        <div className="space-y-6">
          <SimulationControlPanel
            simulation={simulation}
            isPending={control.isPending}
            onControl={(payload) => control.mutate(payload)}
          />
          <OperatorActivityPanel
            simulation={simulation}
            activity={overview.operator_activity}
          />
          <IncidentHandoffPanel handoff={overview.incident_handoff} />
          <ScenarioPlaybooksPanel
            simulation={simulation}
            isPending={control.isPending}
            onRunPlaybook={runPlaybook}
          />
        </div>
      </div>
    </div>
  )
}
