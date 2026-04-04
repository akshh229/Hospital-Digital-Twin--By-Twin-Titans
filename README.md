# Hospital Digital Twin 🏥💻

**Team Name:** Twin Titans
**Event:** The Rosetta Code Hackathon (NIT Hamirpur)
**Challenge:** Twin-Titans Lazarus - Round 2

A complete Hospital Digital Twin engineered to simulate, predict, and manage the logistical operations of the St. Jude’s ICU under extreme duress.

---

## 📋 Overview
The Hospital Digital Twin solves a critical healthcare crisis: managing a highly volatile ICU ecosystem. Continuous patient admissions, fluctuating vitals, and complex medication schedules actively drain critical resources. This system intelligently and autonomously handles these constraints under simulated extreme stress scenarios.

## ✨ Core Features

### Backend Logic (Automated Ward Allocation)
*   **Dynamic Routing:** Automatically route patients to appropriate wards/beds upon admission.
*   **Risk Scoring:** Calculate real-time risk scores for patients dynamically based on fluctuating vitals and severity.
*   **Capacity Management:** Assess live bed capacity across the ICU to safely allocate incoming patients without overallocating resources.

### Frontend UI (Operational Command Dashboard)
*   **Live ICU Bed Heatmap:** Real-time visual representation of bed occupancy and patient severity.
*   **Predictive Resource Graphs:** Trend lines forecasting the drain on critical resources (ventilators, medications, staff).
*   **Patient Flow Timeline:** Chronological tracking of patient movements, admissions, discharges, and critical events.
*   **Simulation Control Panel:** Interface to trigger "extreme duress" scenarios (mass casualties, resource drops) to test system resilience.

---

## 🛠 Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (Relational Data & Models)
- **Caching/PubSub:** Redis (Real-time messaging, fast data access)

### Frontend
- **Framework:** React.js
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **Real-Time Integration:** WebSockets (Seamless bidirectional data flow)

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy / Web Server:** Nginx

---

## 🚀 Getting Started

The project is fully containerized for a smooth setup experience utilizing Docker Compose.

### Prerequisites
- Docker & Docker Compose installed on your system.
- Git (for cloning the repository).

### Installation & Run

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd "Hospital Digital Twin"
   ```

2. **Start the Infrastructure**
   The entire stack (Frontend, Backend, PostgreSQL, Redis, and Nginx) is orchestrated via Docker Compose.
   ```bash
   docker-compose up --build -d
   ```

3. **Access the Application**
   - **Frontend Dashboard:** `http://localhost` (Served via Nginx)
   - **Backend API Docs:** `http://localhost/api/docs` (FastAPI Swagger UI)
   *(Port configurations map through Nginx based on `docker-compose.yml` settings)*

4. **Stopping the Application**
   ```bash
   docker-compose down
   ```

---

## 🏗 System Architecture & Data Flow

1. **Simulation Control Panel** sends stress signals (e.g., mass admissions) to the Backend.
2. **Backend Engine:**
    - Generates simulated patient vitals.
    - Evaluates patient condition via the **Risk Scoring Module**.
    - Assigns beds using the **Ward Allocation Algorithm**.
3. **Real-Time Pipeline:** The backend broadcasts continuous updates via WebSockets, utilizing Redis PubSub for scalable message brokering.
4. **Frontend Dashboard:** Subscribes to the WebSocket feeds, updating the Live Heatmap, Consumption Graphs, and Flow Timeline instantly with zero visual lag.

---

## 🎯 Success Metrics
*   Accurate and immediate routing of high-risk patients.
*   Zero system crashes during stress simulation (Mass casualty triggers).
*   Dashboard updates reflecting backend state changes within milliseconds.

---
*Built with ❤️ by **Twin Titans** for the Rosetta Code Hackathon @ NIT Hamirpur.*