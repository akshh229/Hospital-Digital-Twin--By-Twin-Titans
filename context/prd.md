# Hospital Digital Twin - Product Requirements Document (PRD)

## 1. Overview
**Project Name**: Hospital Digital Twin 
**Challenge**: Twin-Titans Lazarus - Round 2
**Mission**: Engineer a complete Hospital Digital Twin to simulate, predict, and manage the logistical operations of the St. Jude’s ICU under extreme duress.

## 2. Problem Statement (The Technical Crisis)
The environment involves managing a highly volatile ecosystem where continuous patient admissions, fluctuating vitals, and complex medication schedules actively drain critical resources. The system needs to intelligently and autonomously handle these constraints under stress.

## 3. Core Features & Deliverables

### 3.1. Automated Ward Allocation Algorithm (Backend / Logic Focus)
*   **Dynamic Routing**: Automatically route patients to appropriate wards/beds upon admission.
*   **Risk Scoring**: Calculate real-time risk scores for patients dynamically based on fluctuating vitals and condition severity.
*   **Real-Time Capacity Management**: Asses live bed capacity across the ICU to allocate incoming patients without overallocating resources.

### 3.2. Operational Command Dashboard (Frontend / UI Focus)
*   **Live ICU Bed Heatmap**: A visual, real-time representation of bed occupancy and patient severity across the ICU floor.
*   **Predictive Resource Consumption Graphs**: Trend lines and predictive analytics forecasting the drain on critical resources (e.g., ventilators, medications, staff).
*   **Patient Flow Timeline**: A chronological and real-time tracker of patient movements, admissions, discharges, and critical events.
*   **Interactive Simulation Control Panel**: A control module allowing operators (or judges) to trigger "extreme duress" scenarios, such as mass casualty events, sudden drops in resources, or rapid vital fluctuations, to test the system's resilience.

## 4. Constraints & Non-Functional Requirements
*   **Real-time Capabilities**: Data must flow bidirectionally in real-time or near real-time (WebSockets are recommended).
*   **Scalability & Resilience**: The system must sustain volatile bursts of simulated patient data without degrading performance.

## 5. Success Metrics
*   Accurate and immediate routing of high-risk patients.
*   Zero system crashes during stress simulation (Simulation Control Panel triggers).
*   Dashboard updates reflecting backend state changes within milliseconds.
