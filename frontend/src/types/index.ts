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
