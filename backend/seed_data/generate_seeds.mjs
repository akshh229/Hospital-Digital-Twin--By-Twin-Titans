import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function encryptMedication(plainText, age) {
  const shift = age % 26;
  return plainText
    .toUpperCase()
    .split("")
    .map((ch) => {
      if (/[A-Z]/.test(ch)) {
        const pos = ch.charCodeAt(0) - 65;
        return String.fromCharCode(65 + ((pos + shift) % 26));
      }
      return ch;
    })
    .join("");
}

function encodeTelemetry(bpm, spo2) {
  const bpmHex = bpm.toString(16).padStart(4, "0");
  const spo2Hex = spo2.toString(16).padStart(4, "0");
  return bpmHex + spo2Hex;
}

const PATIENTS = 20;
const COLLIDING_IDS = 5;

const MEDICATIONS = [
  "ASPIRIN", "INSULIN", "MORPHINE", "WARFARIN", "LISINOPRIL",
  "METFORMIN", "ATORVASTATIN", "AMLODIPINE", "OMEPRAZOLE", "GABAPENTIN",
];

const WARDS = ["ICU-1", "ICU-2", "ICU-3", "Ward-4", "Ward-5", "ER"];

const FIRST_NAMES = [
  "John","Jane","Robert","Maria","David","Sarah","Michael","Emily",
  "James","Linda","William","Patricia","Richard","Barbara","Joseph",
  "Elizabeth","Thomas","Susan","Charles","Jessica",
];
const LAST_NAMES = [
  "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
  "Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez",
  "Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
];

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
function randChoice(arr) {
  return arr[randInt(0, arr.length - 1)];
}

// Generate patients
const patients = [];
const usedNames = new Set();

for (let i = 0; i < PATIENTS; i++) {
  let rawId;
  if (i < COLLIDING_IDS * 2) {
    rawId = `P${String(Math.floor(i / 2) + 1).padStart(5, "0")}`;
  } else {
    rawId = `P${String(i + 1).padStart(5, "0")}`;
  }
  const age = randInt(18, 85);
  let name;
  do {
    name = `${randChoice(FIRST_NAMES)} ${randChoice(LAST_NAMES)}`;
  } while (usedNames.has(name));
  usedNames.add(name);
  const nameCipher = name.toUpperCase().replace(/ /g, "");
  patients.push({ patient_raw_id: rawId, name_cipher: nameCipher, age, ward_code: randChoice(WARDS) });
}

// Write patient_demographics.csv
let csv = "patient_raw_id,name_cipher,age,ward_code\n";
for (const p of patients) {
  csv += `${p.patient_raw_id},${p.name_cipher},${p.age},${p.ward_code}\n`;
}
writeFileSync(join(__dirname, "patient_demographics.csv"), csv);
console.log(`  Generated ${patients.length} patients`);

// Generate telemetry (1000 samples per patient)
const telemetryLines = ["patient_raw_id,timestamp,hex_payload,source_device"];
const startTime = new Date(Date.now() - 24 * 60 * 60 * 1000);

for (const patient of patients) {
  const patientIdx = parseInt(patient.patient_raw_id.slice(1)) - 1;
  let baseBpm;
  if (patientIdx < COLLIDING_IDS * 2) {
    baseBpm = patientIdx % 2 === 0 ? 70 : 75;
  } else {
    baseBpm = randInt(60, 90);
  }

  for (let j = 0; j < 1000; j++) {
    const ts = new Date(startTime.getTime() + j * 1.44 * 60000);
    let bpm = baseBpm + randInt(-10, 10);
    const spo2 = randInt(94, 100);
    let hexPayload;

    if (Math.random() < 0.05) {
      if (Math.random() < 0.5) {
        hexPayload = "DEADBEEF";
      } else {
        bpm = randInt(250, 300);
        hexPayload = encodeTelemetry(bpm, spo2);
      }
    } else {
      hexPayload = encodeTelemetry(bpm, spo2);
    }

    telemetryLines.push(
      `${patient.patient_raw_id},${ts.toISOString()},${hexPayload},MONITOR_${randInt(1, 10)}`
    );
  }
}
writeFileSync(join(__dirname, "telemetry_logs.csv"), telemetryLines.join("\n"));
console.log(`  Generated ${telemetryLines.length - 1} telemetry samples`);

// Generate prescriptions
const prescriptionLines = ["patient_raw_id,timestamp,age,med_cipher_text,dosage,route"];
for (const patient of patients) {
  const numMeds = randInt(3, 8);
  for (let m = 0; m < numMeds; m++) {
    const medName = randChoice(MEDICATIONS);
    const medCipher = encryptMedication(medName, patient.age);
    const ts = new Date(Date.now() - randInt(1, 72) * 3600000);
    const dosage = `${randChoice([2, 5, 10, 25, 50, 100])}mg`;
    const route = randChoice(["PO", "IV", "SC", "IM"]);
    prescriptionLines.push(
      `${patient.patient_raw_id},${ts.toISOString()},${patient.age},${medCipher},${dosage},${route}`
    );
  }
}
writeFileSync(join(__dirname, "prescription_audit.csv"), prescriptionLines.join("\n"));
console.log(`  Generated ${prescriptionLines.length - 1} prescriptions`);

console.log("\nSeed data generated successfully!");
console.log("  - patient_demographics.csv");
console.log("  - telemetry_logs.csv");
console.log("  - prescription_audit.csv");
