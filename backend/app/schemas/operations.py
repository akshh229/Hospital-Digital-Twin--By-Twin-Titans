"""Schemas for the ICU digital twin operations center."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SimulationStateResponse(BaseModel):
    class ActiveInterventionResponse(BaseModel):
        id: str
        label: str
        value: str
        effect: str
        can_step_down: bool = False
        step_down_label: str | None = None
        can_clear: bool = False
        clear_label: str | None = None

    is_paused: bool
    speed: float
    active_scenario: str
    crisis_level: int
    crisis_label: str
    virtual_admissions: int
    active_interventions: list[ActiveInterventionResponse] = Field(default_factory=list)
    updated_at: datetime
    last_action: str
    last_action_label: str
    last_action_at: datetime | None = None


class OperatorActivityEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    action_key: str
    action_label: str
    event_type: Literal["simulation", "crisis", "intervention"]
    severity: Literal["normal", "warning", "critical"]
    title: str
    description: str
    intervention_id: str | None = None
    scenario_label: str | None = None
    speed: float | None = None


class IncidentHandoffResponse(BaseModel):
    class SnapshotMetricResponse(BaseModel):
        key: str
        label: str
        value: str

    title: str
    generated_at: datetime
    status: Literal["stable", "watch", "critical"]
    status_label: str
    scenario_label: str
    summary: str
    command_snapshot: list[SnapshotMetricResponse] = Field(default_factory=list)
    immediate_risks: list[str] = Field(default_factory=list)
    active_interventions: list[str] = Field(default_factory=list)
    recent_actions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    export_filename: str
    markdown: str


class BedPatientResponse(BaseModel):
    patient_id: str
    patient_raw_id: str
    patient_name: str | None = None
    age: int | None = None
    ward: str | None = None
    parity_flag: str
    last_bpm: int | None = None
    last_oxygen: int | None = None
    has_active_alert: bool
    risk_score: int
    risk_label: str
    recommended_unit: str
    risk_reasons: list[str] = Field(default_factory=list)


class BedTileResponse(BaseModel):
    bed_id: str
    zone: str
    status: Literal["occupied", "available"]
    assignment_reason: str
    patient: BedPatientResponse | None = None


class TriageQueueEntryResponse(BaseModel):
    patient_id: str
    patient_name: str | None = None
    patient_raw_id: str
    risk_score: int
    risk_label: str
    queue_reason: str
    recommended_unit: str
    risk_reasons: list[str] = Field(default_factory=list)


class ResourceCardResponse(BaseModel):
    resource_key: str
    label: str
    subtitle: str
    available: int
    capacity: int
    unit: str
    utilization_percent: int
    status: Literal["normal", "warning", "critical"]
    trend: Literal["stable", "rising", "falling"]


class ResourceForecastPointResponse(BaseModel):
    time_label: str
    oxygen_network_percent: int
    staff_load_percent: int
    ventilator_usage_percent: int
    vasopressor_stock_percent: int


class TimelineEventResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    severity: Literal["normal", "warning", "critical"]
    title: str
    description: str
    patient_id: str | None = None
    bed_id: str | None = None


class OperationsBriefingResponse(BaseModel):
    headline: str
    summary: str
    changes: list[str] = Field(default_factory=list)


class OperationsTrustResponse(BaseModel):
    telemetry_state: Literal["live", "watch", "paused"]
    simulator_status: Literal["running", "paused"]
    data_source: str
    confidence_label: Literal["high", "medium", "low"]
    confidence_reason: str
    last_telemetry_at: datetime | None = None
    telemetry_age_seconds: int | None = None


class RecommendedActionResponse(BaseModel):
    class ProjectedMetricResponse(BaseModel):
        key: str
        label: str
        current_value: int
        projected_value: int
        delta: int
        unit: str

    class ObservedMetricResponse(BaseModel):
        key: str
        label: str
        baseline_value: int
        current_value: int
        delta: int
        unit: str

    id: str
    action_type: Literal["intervention", "control", "advisory"]
    control_action: (
        Literal["pause", "resume", "set_speed", "inject_crisis", "apply_intervention", "reset"]
        | None
    ) = None
    priority: Literal["critical", "warning", "normal"]
    title: str
    rationale: str
    owner: str
    state: Literal["recommended", "active", "saturated", "recently_applied"]
    state_label: str
    state_reason: str
    can_apply: bool = True
    apply_label: str | None = None
    projected_summary: str
    projected_window_minutes: int
    projected_metrics: list[ProjectedMetricResponse] = Field(default_factory=list)
    observed_summary: str | None = None
    observed_metrics: list[ObservedMetricResponse] = Field(default_factory=list)


class ScenarioDeltaMetricResponse(BaseModel):
    key: str
    label: str
    baseline_value: int
    current_value: int
    delta: int
    direction: Literal["up", "down", "flat"]
    status: Literal["improved", "degraded", "unchanged"]


class ScenarioComparisonResponse(BaseModel):
    baseline_label: str
    current_label: str
    summary_metrics: list[ScenarioDeltaMetricResponse]
    resource_metrics: list[ScenarioDeltaMetricResponse]


class IncidentReplayFrameResponse(BaseModel):
    id: str
    timestamp: datetime
    title: str
    severity: Literal["normal", "warning", "critical"]
    phase_label: str
    summary: str
    icu_occupied: int
    overflow_patients: int
    active_alerts: int
    attention_patients: int
    focus_note: str


class OperationsSummaryResponse(BaseModel):
    total_patients: int
    icu_capacity: int
    icu_occupied: int
    overflow_patients: int
    active_alerts: int
    average_risk_score: int
    attention_patients: int
    updated_at: datetime


class OperationsOverviewResponse(BaseModel):
    summary: OperationsSummaryResponse
    simulation: SimulationStateResponse
    briefing: OperationsBriefingResponse
    trust: OperationsTrustResponse
    recommended_actions: list[RecommendedActionResponse]
    scenario_comparison: ScenarioComparisonResponse
    replay_frames: list[IncidentReplayFrameResponse]
    bed_heatmap: list[BedTileResponse]
    triage_queue: list[TriageQueueEntryResponse]
    resource_cards: list[ResourceCardResponse]
    resource_forecast: list[ResourceForecastPointResponse]
    timeline: list[TimelineEventResponse]
    operator_activity: list[OperatorActivityEntryResponse]
    incident_handoff: IncidentHandoffResponse


class SimulationControlRequest(BaseModel):
    action: Literal[
        "pause",
        "resume",
        "set_speed",
        "inject_crisis",
        "apply_intervention",
        "step_down_intervention",
        "clear_intervention",
        "reset",
    ]
    speed: float | None = Field(default=None, ge=0.5, le=4.0)
    scenario: str | None = Field(default=None, max_length=60)
    severity: Literal["minor", "major", "extreme"] | None = None
    patient_count: int | None = Field(default=None, ge=1, le=12)
    intervention_id: str | None = Field(default=None, max_length=80)
