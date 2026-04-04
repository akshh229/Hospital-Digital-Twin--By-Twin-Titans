export interface Patient {
  patient_id: string
  patient_raw_id: string
  parity_flag: string
  name: string | null
  age: number | null
  ward: string | null
  last_bpm: number | null
  last_oxygen: number | null
  last_vitals_timestamp: string | null
  quality_flag: string | null
  prescription_count: number
  has_active_alert: boolean
  identity_confidence?: number
  identity_sample_count?: number
}

export type RealtimeConnectionState =
  | 'connecting'
  | 'reconnecting'
  | 'live'
  | 'offline'

export interface VitalsDataPoint {
  timestamp: string
  bpm: number | null
  oxygen: number | null
  quality_flag: string
}

export interface VitalsResponse {
  patient_id: string
  start_time: string
  end_time: string
  data: VitalsDataPoint[]
}

export interface Prescription {
  id: number
  timestamp: string
  age: number
  med_cipher_text: string
  med_decoded_name: string | null
  dosage: string | null
  route: string | null
}

export interface Alert {
  id: number
  patient_id: string
  alert_type: string
  opened_at: string
  last_bpm: number | null
  last_oxygen: number | null
  status: string
  consecutive_abnormal_count: number
  patient_name: string | null
  age: number | null
  ward: string | null
}

export interface AlertHistory {
  id: number
  opened_at: string
  closed_at: string | null
  duration_minutes: number | null
  last_bpm: number
  last_oxygen: number
  status: string
}

export interface VitalsUpdateMessage {
  type: 'vitals_update'
  patient_id: string
  timestamp: string
  bpm: number
  oxygen: number
}

export interface AlertOpenedMessage {
  type: 'alert_opened'
  patient_id: string
  patient_name: string
  last_bpm: number
}

export interface AlertClosedMessage {
  type: 'alert_closed'
  patient_id: string
}

export interface PatientsSnapshotMessage {
  type: 'patients_snapshot'
  patients: Patient[]
}

export interface AlertsSnapshotMessage {
  type: 'alerts_snapshot'
  alerts: Alert[]
}

export interface TelemetrySimulationResponse {
  patient_id: string
  patient_raw_id: string
  requested_bpm: number
  applied_bpm: number
  oxygen: number
  parity_flag: string
  adjusted_for_identity: boolean
  timestamp: string
  alert_status: string | null
}

export interface ActiveIntervention {
  id: string
  label: string
  value: string
  effect: string
}

export interface SimulationState {
  is_paused: boolean
  speed: number
  active_scenario: string
  crisis_level: number
  crisis_label: string
  virtual_admissions: number
  active_interventions: ActiveIntervention[]
  updated_at: string
  last_action: string
}

export interface BedPatient {
  patient_id: string
  patient_raw_id: string
  patient_name: string | null
  age: number | null
  ward: string | null
  parity_flag: string
  last_bpm: number | null
  last_oxygen: number | null
  has_active_alert: boolean
  risk_score: number
  risk_label: string
  recommended_unit: string
  risk_reasons: string[]
}

export interface BedTile {
  bed_id: string
  zone: string
  status: 'occupied' | 'available'
  assignment_reason: string
  patient: BedPatient | null
}

export interface TriageQueueEntry {
  patient_id: string
  patient_name: string | null
  patient_raw_id: string
  risk_score: number
  risk_label: string
  queue_reason: string
  recommended_unit: string
  risk_reasons: string[]
}

export interface ResourceCard {
  resource_key: string
  label: string
  subtitle: string
  available: number
  capacity: number
  unit: string
  utilization_percent: number
  status: 'normal' | 'warning' | 'critical'
  trend: 'stable' | 'rising' | 'falling'
}

export interface ResourceForecastPoint {
  time_label: string
  oxygen_network_percent: number
  staff_load_percent: number
  ventilator_usage_percent: number
  vasopressor_stock_percent: number
}

export interface TimelineEvent {
  id: string
  timestamp: string
  event_type: string
  severity: 'normal' | 'warning' | 'critical'
  title: string
  description: string
  patient_id: string | null
  bed_id: string | null
}

export interface OperationsBriefing {
  headline: string
  summary: string
  changes: string[]
}

export interface OperationsTrust {
  telemetry_state: 'live' | 'watch' | 'paused'
  simulator_status: 'running' | 'paused'
  data_source: string
  confidence_label: 'high' | 'medium' | 'low'
  confidence_reason: string
  last_telemetry_at: string | null
  telemetry_age_seconds: number | null
}

export interface RecommendedAction {
  action_type: 'intervention' | 'control' | 'advisory'
  control_action?:
    | 'pause'
    | 'resume'
    | 'set_speed'
    | 'inject_crisis'
    | 'apply_intervention'
    | 'reset'
  projected_summary: string
  projected_window_minutes: number
  projected_metrics: Array<{
    key: string
    label: string
    current_value: number
    projected_value: number
    delta: number
    unit: string
  }>
  observed_summary?: string | null
  observed_metrics: Array<{
    key: string
    label: string
    baseline_value: number
    current_value: number
    delta: number
    unit: string
  }>
  id: string
  priority: 'critical' | 'warning' | 'normal'
  title: string
  rationale: string
  owner: string
  state: 'recommended' | 'active' | 'saturated' | 'recently_applied'
  state_label: string
  state_reason: string
  can_apply: boolean
  apply_label?: string | null
}

export interface ScenarioDeltaMetric {
  key: string
  label: string
  baseline_value: number
  current_value: number
  delta: number
  direction: 'up' | 'down' | 'flat'
  status: 'improved' | 'degraded' | 'unchanged'
}

export interface ScenarioComparison {
  baseline_label: string
  current_label: string
  summary_metrics: ScenarioDeltaMetric[]
  resource_metrics: ScenarioDeltaMetric[]
}

export interface IncidentReplayFrame {
  id: string
  timestamp: string
  title: string
  severity: 'normal' | 'warning' | 'critical'
  phase_label: string
  summary: string
  icu_occupied: number
  overflow_patients: number
  active_alerts: number
  attention_patients: number
  focus_note: string
}

export interface OperationsSummary {
  total_patients: number
  icu_capacity: number
  icu_occupied: number
  overflow_patients: number
  active_alerts: number
  average_risk_score: number
  attention_patients: number
  updated_at: string
}

export interface OperationsOverview {
  summary: OperationsSummary
  simulation: SimulationState
  briefing: OperationsBriefing
  trust: OperationsTrust
  recommended_actions: RecommendedAction[]
  scenario_comparison: ScenarioComparison
  replay_frames: IncidentReplayFrame[]
  bed_heatmap: BedTile[]
  triage_queue: TriageQueueEntry[]
  resource_cards: ResourceCard[]
  resource_forecast: ResourceForecastPoint[]
  timeline: TimelineEvent[]
}

export interface OpsSnapshotMessage {
  type: 'ops_snapshot'
  overview: OperationsOverview
}

export interface SimulationControlRequest {
  action:
    | 'pause'
    | 'resume'
    | 'set_speed'
    | 'inject_crisis'
    | 'apply_intervention'
    | 'reset'
  speed?: number
  scenario?: string
  severity?: 'minor' | 'major' | 'extreme'
  patient_count?: number
  intervention_id?: string
}
