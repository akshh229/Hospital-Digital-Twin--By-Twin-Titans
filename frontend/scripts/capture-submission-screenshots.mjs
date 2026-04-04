import { createServer } from 'node:http'
import { promises as fs } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')
const distDir = path.join(projectRoot, 'dist')
const screenshotsDir = path.resolve(projectRoot, '..', 'screenshots')
const port = 4173
const baseUrl = `http://127.0.0.1:${port}`

const leadPatientId = '00000000-0000-4000-8000-000000000101'
const supportPatientId = '00000000-0000-4000-8000-000000000102'
const overflowPatientId = '00000000-0000-4000-8000-000000000103'

function isoAt(offsetMinutes) {
  const now = new Date('2026-04-04T12:00:00.000Z')
  now.setUTCMinutes(now.getUTCMinutes() + offsetMinutes)
  return now.toISOString()
}

function buildLeadPatient() {
  return {
    patient_id: leadPatientId,
    patient_raw_id: 'SJ-1042',
    parity_flag: 'even',
    name: 'Aarav Patel',
    age: 56,
    ward: 'ICU North',
    last_bpm: 128,
    last_oxygen: 88,
    last_vitals_timestamp: isoAt(-2),
    quality_flag: 'good',
    prescription_count: 4,
    has_active_alert: true,
    identity_confidence: 0.93,
    identity_sample_count: 10,
  }
}

function buildSupportPatient() {
  return {
    patient_id: supportPatientId,
    patient_raw_id: 'SJ-1178',
    parity_flag: 'odd',
    name: 'Maya Rao',
    age: 42,
    ward: 'Step-down',
    last_bpm: 102,
    last_oxygen: 94,
    last_vitals_timestamp: isoAt(-4),
    quality_flag: 'good',
    prescription_count: 2,
    has_active_alert: false,
    identity_confidence: 0.88,
    identity_sample_count: 9,
  }
}

function buildOverflowPatient() {
  return {
    patient_id: overflowPatientId,
    patient_raw_id: 'SJ-1251',
    parity_flag: 'even',
    name: 'Kabir Singh',
    age: 63,
    ward: 'ED Transfer',
    last_bpm: 116,
    last_oxygen: 90,
    last_vitals_timestamp: isoAt(-3),
    quality_flag: 'good',
    prescription_count: 3,
    has_active_alert: true,
    identity_confidence: 0.9,
    identity_sample_count: 8,
  }
}

function buildAlerts(mode) {
  const base = [
    {
      id: 41,
      patient_id: leadPatientId,
      alert_type: 'tachycardia',
      opened_at: isoAt(-14),
      last_bpm: mode === 'baseline' ? 112 : 128,
      last_oxygen: mode === 'baseline' ? 93 : 88,
      status: 'open',
      consecutive_abnormal_count: 3,
      patient_name: 'Aarav Patel',
      age: 56,
      ward: 'ICU North',
    },
  ]

  if (mode === 'baseline') {
    return base
  }

  return [
    ...base,
    {
      id: 42,
      patient_id: overflowPatientId,
      alert_type: 'hypoxia',
      opened_at: isoAt(-10),
      last_bpm: 118,
      last_oxygen: 85,
      status: 'open',
      consecutive_abnormal_count: 4,
      patient_name: 'Kabir Singh',
      age: 63,
      ward: 'ED Transfer',
    },
    {
      id: 43,
      patient_id: supportPatientId,
      alert_type: 'resource_watch',
      opened_at: isoAt(-8),
      last_bpm: 109,
      last_oxygen: 91,
      status: 'open',
      consecutive_abnormal_count: 2,
      patient_name: 'Maya Rao',
      age: 42,
      ward: 'Step-down',
    },
  ]
}

function buildResourceForecast(mode, speed = 1) {
  const baseline = [
    { time_label: '12:00', oxygen_network_percent: 84, staff_load_percent: 58, ventilator_usage_percent: 34, vasopressor_stock_percent: 79 },
    { time_label: '14:00', oxygen_network_percent: 80, staff_load_percent: 62, ventilator_usage_percent: 38, vasopressor_stock_percent: 74 },
    { time_label: '16:00', oxygen_network_percent: 76, staff_load_percent: 67, ventilator_usage_percent: 42, vasopressor_stock_percent: 70 },
    { time_label: '18:00', oxygen_network_percent: 72, staff_load_percent: 71, ventilator_usage_percent: 46, vasopressor_stock_percent: 66 },
    { time_label: '20:00', oxygen_network_percent: 69, staff_load_percent: 75, ventilator_usage_percent: 50, vasopressor_stock_percent: 63 },
    { time_label: '22:00', oxygen_network_percent: 65, staff_load_percent: 79, ventilator_usage_percent: 55, vasopressor_stock_percent: 58 },
  ]

  if (mode === 'baseline') {
    return baseline.map((point) => ({
      ...point,
      staff_load_percent: Math.min(100, Math.round(point.staff_load_percent * speed)),
    }))
  }

  return [
    { time_label: '12:00', oxygen_network_percent: 54, staff_load_percent: 79, ventilator_usage_percent: 62, vasopressor_stock_percent: 61 },
    { time_label: '14:00', oxygen_network_percent: 47, staff_load_percent: 84, ventilator_usage_percent: 68, vasopressor_stock_percent: 55 },
    { time_label: '16:00', oxygen_network_percent: 40, staff_load_percent: 88, ventilator_usage_percent: 74, vasopressor_stock_percent: 49 },
    { time_label: '18:00', oxygen_network_percent: 34, staff_load_percent: 92, ventilator_usage_percent: 79, vasopressor_stock_percent: 44 },
    { time_label: '20:00', oxygen_network_percent: 28, staff_load_percent: 95, ventilator_usage_percent: 84, vasopressor_stock_percent: 39 },
    { time_label: '22:00', oxygen_network_percent: 22, staff_load_percent: 98, ventilator_usage_percent: 89, vasopressor_stock_percent: 33 },
  ].map((point) => ({
    ...point,
    staff_load_percent: Math.min(100, Math.round(point.staff_load_percent * Math.max(speed / 1.5, 1))),
  }))
}

function buildOverview({ mode = 'baseline', speed = 1, paused = false } = {}) {
  const lead = buildLeadPatient()
  const support = buildSupportPatient()
  const overflow = buildOverflowPatient()

  const leadBedPatient = {
    patient_id: lead.patient_id,
    patient_raw_id: lead.patient_raw_id,
    patient_name: lead.name,
    age: lead.age,
    ward: lead.ward,
    parity_flag: lead.parity_flag,
    last_bpm: mode === 'baseline' ? 112 : 128,
    last_oxygen: mode === 'baseline' ? 93 : 88,
    has_active_alert: true,
    risk_score: mode === 'baseline' ? 74 : 92,
    risk_label: mode === 'baseline' ? 'High' : 'Critical',
    recommended_unit: 'ICU',
  }

  const supportBedPatient = {
    patient_id: support.patient_id,
    patient_raw_id: support.patient_raw_id,
    patient_name: support.name,
    age: support.age,
    ward: support.ward,
    parity_flag: support.parity_flag,
    last_bpm: mode === 'baseline' ? 96 : 109,
    last_oxygen: mode === 'baseline' ? 96 : 91,
    has_active_alert: mode !== 'baseline',
    risk_score: mode === 'baseline' ? 46 : 71,
    risk_label: mode === 'baseline' ? 'Guarded' : 'High',
    recommended_unit: mode === 'baseline' ? 'Observation' : 'ICU',
  }

  const bed_heatmap = [
    {
      bed_id: 'ICU-01',
      zone: 'North Pod',
      status: 'occupied',
      assignment_reason: mode === 'baseline' ? 'High acuity routing' : 'Alert escalation routing',
      patient: leadBedPatient,
    },
    {
      bed_id: 'ICU-02',
      zone: 'North Pod',
      status: 'occupied',
      assignment_reason: mode === 'baseline' ? 'Guarded acuity routing' : 'High acuity routing',
      patient: supportBedPatient,
    },
    {
      bed_id: 'ICU-03',
      zone: 'North Pod',
      status: 'occupied',
      assignment_reason: 'Critical respiratory support',
      patient: {
        patient_id: '00000000-0000-4000-8000-000000000104',
        patient_raw_id: 'SJ-1183',
        patient_name: 'Ira Mehta',
        age: 67,
        ward: 'ICU South',
        parity_flag: 'even',
        last_bpm: 121,
        last_oxygen: 86,
        has_active_alert: true,
        risk_score: 88,
        risk_label: 'Critical',
        recommended_unit: 'ICU',
      },
    },
  ]

  for (let index = 4; index <= 12; index += 1) {
    bed_heatmap.push({
      bed_id: `ICU-${String(index).padStart(2, '0')}`,
      zone: index <= 6 ? 'North Pod' : 'South Pod',
      status: index <= (mode === 'baseline' ? 7 : 10) ? 'occupied' : 'available',
      assignment_reason:
        index <= (mode === 'baseline' ? 7 : 10)
          ? 'Monitored allocation'
          : 'Ready for incoming critical admissions',
      patient:
        index <= (mode === 'baseline' ? 7 : 10)
          ? {
              patient_id: `00000000-0000-4000-8000-0000000001${index}`,
              patient_raw_id: `SJ-11${70 + index}`,
              patient_name: `Patient ${index}`,
              age: 38 + index,
              ward: 'ICU Overflow',
              parity_flag: index % 2 === 0 ? 'even' : 'odd',
              last_bpm: 82 + index,
              last_oxygen: 95 - Math.min(index, 4),
              has_active_alert: false,
              risk_score: 40 + index,
              risk_label: index > 8 ? 'High' : 'Guarded',
              recommended_unit: index > 8 ? 'Step-down' : 'Observation',
            }
          : null,
    })
  }

  const triageQueue =
    mode === 'baseline'
      ? [
          {
            patient_id: overflow.patient_id,
            patient_name: overflow.name,
            patient_raw_id: overflow.patient_raw_id,
            risk_score: 68,
            risk_label: 'High',
            queue_reason: 'Step-down demand exceeds live ICU capacity',
            recommended_unit: 'Step-down',
          },
        ]
      : [
          {
            patient_id: overflow.patient_id,
            patient_name: overflow.name,
            patient_raw_id: overflow.patient_raw_id,
            risk_score: 86,
            risk_label: 'Critical',
            queue_reason: 'ICU demand exceeds live bed capacity during oxygen shortage',
            recommended_unit: 'ICU',
          },
          {
            patient_id: '00000000-0000-4000-8000-000000000105',
            patient_name: 'Nina Das',
            patient_raw_id: 'SJ-1307',
            risk_score: 78,
            risk_label: 'High',
            queue_reason: 'Mechanical support capacity is saturated',
            recommended_unit: 'ICU',
          },
        ]

  const resourceCards =
    mode === 'baseline'
      ? [
          { resource_key: 'oxygen_network', label: 'Oxygen network', subtitle: 'Central line reserve', available: 84, capacity: 100, unit: '%', utilization_percent: 84, status: 'normal', trend: 'stable' },
          { resource_key: 'ventilators', label: 'Ventilator bank', subtitle: 'Available mechanical support units', available: 7, capacity: 12, unit: 'units', utilization_percent: 58, status: 'warning', trend: 'rising' },
          { resource_key: 'critical_care_nurses', label: 'Critical care nurses', subtitle: 'Staffing headroom on shift', available: 9, capacity: 18, unit: 'staff', utilization_percent: 50, status: 'normal', trend: 'stable' },
          { resource_key: 'vasopressor_stock', label: 'Vasopressor stock', subtitle: 'Estimated medication reserve', available: 79, capacity: 100, unit: '%', utilization_percent: 79, status: 'normal', trend: 'stable' },
        ]
      : [
          { resource_key: 'oxygen_network', label: 'Oxygen network', subtitle: 'Central line reserve', available: 54, capacity: 100, unit: '%', utilization_percent: 54, status: 'warning', trend: 'falling' },
          { resource_key: 'ventilators', label: 'Ventilator bank', subtitle: 'Available mechanical support units', available: 3, capacity: 12, unit: 'units', utilization_percent: 25, status: 'critical', trend: 'falling' },
          { resource_key: 'critical_care_nurses', label: 'Critical care nurses', subtitle: 'Staffing headroom on shift', available: 4, capacity: 18, unit: 'staff', utilization_percent: 22, status: 'critical', trend: 'falling' },
          { resource_key: 'vasopressor_stock', label: 'Vasopressor stock', subtitle: 'Estimated medication reserve', available: 61, capacity: 100, unit: '%', utilization_percent: 61, status: 'warning', trend: 'falling' },
        ]

  const timeline =
    mode === 'baseline'
      ? [
          {
            id: 'timeline-1',
            timestamp: isoAt(-20),
            event_type: 'routing',
            severity: 'warning',
            title: 'ICU-01 assigned to Aarav Patel',
            description: 'A high-acuity patient was routed to ICU-01 after telemetry crossed the watch threshold.',
            patient_id: leadPatientId,
            bed_id: 'ICU-01',
          },
          {
            id: 'timeline-2',
            timestamp: isoAt(-18),
            event_type: 'capacity',
            severity: 'warning',
            title: '1 patient waiting for ICU routing',
            description: 'Overflow demand is still manageable but requires close monitoring.',
            patient_id: overflowPatientId,
            bed_id: null,
          },
        ]
      : [
          {
            id: 'timeline-3',
            timestamp: isoAt(-6),
            event_type: 'crisis',
            severity: 'critical',
            title: 'Oxygen network degradation',
            description: 'A respiratory supply failure has been injected into the digital twin affecting multiple live patients.',
            patient_id: null,
            bed_id: null,
          },
          {
            id: 'timeline-4',
            timestamp: isoAt(-5),
            event_type: 'routing',
            severity: 'critical',
            title: 'ICU-01 assigned to Aarav Patel',
            description: 'Risk 92/100 routed through ICU allocation logic under oxygen shortage conditions.',
            patient_id: leadPatientId,
            bed_id: 'ICU-01',
          },
          {
            id: 'timeline-5',
            timestamp: isoAt(-4),
            event_type: 'capacity',
            severity: 'critical',
            title: '2 patients waiting for ICU routing',
            description: 'Overflow demand now exceeds live bed capacity and requires command intervention.',
            patient_id: null,
            bed_id: null,
          },
        ]

  return {
    summary: {
      total_patients: mode === 'baseline' ? 9 : 12,
      icu_capacity: 12,
      icu_occupied: mode === 'baseline' ? 7 : 10,
      overflow_patients: mode === 'baseline' ? 1 : 2,
      active_alerts: mode === 'baseline' ? 1 : 3,
      average_risk_score: mode === 'baseline' ? 57 : 74,
      attention_patients: mode === 'baseline' ? 3 : 6,
      updated_at: isoAt(0),
    },
    simulation: {
      is_paused: paused,
      speed,
      active_scenario: mode === 'baseline' ? 'baseline' : 'oxygen_shortage',
      crisis_level: mode === 'baseline' ? 0 : 3,
      crisis_label: mode === 'baseline' ? 'Nominal operations' : 'Oxygen network degradation',
      virtual_admissions: mode === 'baseline' ? 1 : 5,
      updated_at: isoAt(0),
      last_action: mode === 'baseline' ? 'initialize' : 'inject_crisis',
    },
    bed_heatmap,
    triage_queue: triageQueue,
    resource_cards: resourceCards,
    resource_forecast: buildResourceForecast(mode, speed),
    timeline,
  }
}

function buildVitalsResponse() {
  const points = Array.from({ length: 12 }, (_, index) => ({
    timestamp: isoAt(-60 + index * 5),
    bpm: [94, 97, 102, 108, 111, 116, 120, 126, 128, 124, 121, 118][index],
    oxygen: [96, 96, 95, 94, 92, 91, 90, 88, 87, 88, 89, 90][index],
    quality_flag: 'good',
  }))

  return {
    patient_id: leadPatientId,
    start_time: isoAt(-60),
    end_time: isoAt(-5),
    data: points,
  }
}

const prescriptions = [
  {
    id: 1,
    timestamp: isoAt(-55),
    age: 56,
    med_cipher_text: 'QXOQJYV',
    med_decoded_name: 'HEPARIN',
    dosage: '5000u',
    route: 'IV',
  },
  {
    id: 2,
    timestamp: isoAt(-42),
    age: 56,
    med_cipher_text: 'AFDMDXQFI',
    med_decoded_name: 'MIDAZOLAM',
    dosage: '2mg',
    route: 'IV',
  },
  {
    id: 3,
    timestamp: isoAt(-30),
    age: 56,
    med_cipher_text: 'POJQXKXQBK',
    med_decoded_name: 'VASOPRESSOR',
    dosage: '8mcg/min',
    route: 'Pump',
  },
]

const alertHistory = [
  {
    id: 31,
    opened_at: isoAt(-180),
    closed_at: isoAt(-165),
    duration_minutes: 15,
    last_bpm: 118,
    last_oxygen: 91,
    status: 'closed',
  },
  {
    id: 32,
    opened_at: isoAt(-240),
    closed_at: isoAt(-222),
    duration_minutes: 18,
    last_bpm: 122,
    last_oxygen: 90,
    status: 'acknowledged',
  },
]

async function ensureDirectory(directoryPath) {
  await fs.mkdir(directoryPath, { recursive: true })
}

async function startStaticServer() {
  const mimeTypes = new Map([
    ['.html', 'text/html; charset=utf-8'],
    ['.js', 'text/javascript; charset=utf-8'],
    ['.css', 'text/css; charset=utf-8'],
    ['.svg', 'image/svg+xml'],
    ['.png', 'image/png'],
    ['.json', 'application/json; charset=utf-8'],
  ])

  const server = createServer(async (req, res) => {
    try {
      const requestUrl = new URL(req.url, baseUrl)
      let filePath = path.join(distDir, requestUrl.pathname)

      if (requestUrl.pathname === '/') {
        filePath = path.join(distDir, 'index.html')
      }

      try {
        const stat = await fs.stat(filePath)
        if (stat.isDirectory()) {
          filePath = path.join(filePath, 'index.html')
        }
      } catch {
        filePath = path.join(distDir, 'index.html')
      }

      const ext = path.extname(filePath)
      const body = await fs.readFile(filePath)
      res.writeHead(200, {
        'Content-Type': mimeTypes.get(ext) ?? 'application/octet-stream',
      })
      res.end(body)
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
      res.end(String(error))
    }
  })

  await new Promise((resolve) => server.listen(port, '127.0.0.1', resolve))
  return server
}

async function main() {
  await ensureDirectory(screenshotsDir)

  let currentMode = 'baseline'
  let currentSpeed = 1
  let currentPaused = false

  const server = await startStaticServer()
  const browser = await chromium.launch()
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    colorScheme: 'light',
  })

  await context.addInitScript(() => {
    const sockets = new Set()

    class MockWebSocket {
      static CONNECTING = 0
      static OPEN = 1
      static CLOSING = 2
      static CLOSED = 3

      constructor(url) {
        this.url = url
        this.readyState = MockWebSocket.CONNECTING
        this.onopen = null
        this.onmessage = null
        this.onerror = null
        this.onclose = null

        sockets.add(this)

        window.setTimeout(() => {
          this.readyState = MockWebSocket.OPEN
          this.onopen?.()
          const payload = window.__SCREENSHOT_SOCKET_PAYLOADS__?.[this.url]
          if (payload) {
            this.onmessage?.({ data: JSON.stringify(payload) })
          }
        }, 60)
      }

      send(raw) {
        try {
          const payload = JSON.parse(raw)
          if (payload.type === 'ping') {
            window.setTimeout(() => {
              this.onmessage?.({
                data: JSON.stringify({
                  type: 'pong',
                  timestamp: new Date().toISOString(),
                }),
              })
            }, 20)
          }
        } catch {
          // no-op
        }
      }

      close() {
        this.readyState = MockWebSocket.CLOSED
        sockets.delete(this)
        this.onclose?.({ code: 1000, reason: 'mock-close' })
      }
    }

    window.WebSocket = MockWebSocket
  })

  const page = await context.newPage()

  await page.route('**/*', async (route) => {
    const request = route.request()
    const requestUrl = new URL(request.url())

    const sendJson = async (payload, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(payload),
      })
    }

    if (requestUrl.pathname === '/health') {
      return sendJson({
        status: 'healthy',
        service: 'st-jude-icu-digital-twin-backend',
        version: '1.0.0',
      })
    }

    if (requestUrl.pathname === '/api/ops/overview') {
      return sendJson(buildOverview({
        mode: currentMode,
        speed: currentSpeed,
        paused: currentPaused,
      }))
    }

    if (requestUrl.pathname === '/api/ops/control' && request.method() === 'POST') {
      const payload = JSON.parse(request.postData() ?? '{}')

      if (payload.action === 'pause') {
        currentPaused = true
      } else if (payload.action === 'resume') {
        currentPaused = false
      } else if (payload.action === 'set_speed') {
        currentSpeed = payload.speed ?? currentSpeed
      } else if (payload.action === 'inject_crisis') {
        currentMode = payload.scenario === 'oxygen_shortage' ? 'crisis' : 'crisis'
        currentSpeed = payload.speed ?? currentSpeed
        currentPaused = false
      } else if (payload.action === 'reset') {
        currentMode = 'baseline'
        currentSpeed = 1
        currentPaused = false
      }

      return sendJson(
        buildOverview({
          mode: currentMode,
          speed: currentSpeed,
          paused: currentPaused,
        })
      )
    }

    if (requestUrl.pathname === '/api/alerts') {
      return sendJson(buildAlerts(currentMode))
    }

    if (requestUrl.pathname === '/api/patients') {
      return sendJson([
        buildLeadPatient(),
        buildSupportPatient(),
        buildOverflowPatient(),
      ])
    }

    if (requestUrl.pathname === `/api/patients/${leadPatientId}`) {
      return sendJson(buildLeadPatient())
    }

    if (requestUrl.pathname === `/api/patients/${leadPatientId}/vitals`) {
      return sendJson(buildVitalsResponse())
    }

    if (requestUrl.pathname === `/api/patients/${leadPatientId}/prescriptions`) {
      return sendJson(prescriptions)
    }

    if (requestUrl.pathname === `/api/alerts/history/${leadPatientId}`) {
      return sendJson(alertHistory)
    }

    return route.continue()
  })

  async function setSocketPayloads() {
    const payloads = {
      [`ws://127.0.0.1:${port}/ws/ops/overview`]: {
        type: 'ops_snapshot',
        overview: buildOverview({
          mode: currentMode,
          speed: currentSpeed,
          paused: currentPaused,
        }),
      },
      [`ws://127.0.0.1:${port}/ws/vitals/${leadPatientId}`]: {
        type: 'vitals_update',
        patient_id: leadPatientId,
        timestamp: isoAt(-2),
        bpm: currentMode === 'baseline' ? 112 : 128,
        oxygen: currentMode === 'baseline' ? 93 : 88,
      },
    }

    await page.addInitScript((socketPayloads) => {
      window.__SCREENSHOT_SOCKET_PAYLOADS__ = socketPayloads
    }, payloads)
  }

  await setSocketPayloads()
  await page.goto(baseUrl, { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(400)
  await page.screenshot({
    path: path.join(screenshotsDir, '01-command-center-overview.png'),
  })

  await page.getByRole('button', { name: 'Run playbook' }).nth(1).click()
  await page.waitForTimeout(500)
  await page.screenshot({
    path: path.join(screenshotsDir, '02-command-center-crisis-response.png'),
  })

  await setSocketPayloads()
  await page.goto(`${baseUrl}/patient/${leadPatientId}`, { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(400)
  await page.screenshot({
    path: path.join(screenshotsDir, '03-patient-drilldown.png'),
    fullPage: true,
  })

  await browser.close()
  await new Promise((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve()))
  )

  const files = await fs.readdir(screenshotsDir)
  const generated = files
    .filter((name) => name.endsWith('.png'))
    .sort()

  for (const filename of generated) {
    const stat = await fs.stat(path.join(screenshotsDir, filename))
    console.log(`${filename} - ${(stat.size / 1024 / 1024).toFixed(2)} MB - 2880px wide @ 2x`)
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
