# Project Architecture & Stack

## Tech Stack (Carried over from Round 1)

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Relational Data, Models)
- **Caching/PubSub**: Redis (For fast data access, rate limiting, and real-time messaging)

### Frontend
- **Framework**: React.js
- **Build Tool**: Vite
- **UI Styling**: TailwindCSS (or similar utility-first CSS framework configured in the repo)
- **State Management / Real-time**: WebSockets (likely `socket.io-client` or native WebSockets communicating with FastAPI backend)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server / Reverse Proxy**: Nginx

## Data Flow (High Level)
1. **Simulation Control Panel** -> Sends stress signals (mass admissions, resource drops) to Backend.
2. **Backend Engine**:
    - **Data Generator**: Simulates patient vitals and resource usage.
    - **Risk Scoring Module**: Evaluates patient condition based on vitals.
    - **Ward Allocation Algorithm**: Assigns beds based on Risk Score and Capacity.
3. **Real-time Pipeline**: Backend broadcasts updates via WebSockets utilizing Redis PubSub.
4. **Frontend Dashboard**: Subscribes to WebSockets and updates the Live Heatmap, Consumption Graphs, and Flow Timeline instantly.

## Feature Mapping vs Infrastructure
*   **Heatmap**: Will require a robust state representation of "Beds" and their "Occupancy/Severity" in the DB/Redis.
*   **Predictive Graphs**: Will need an aggregation endpoint and time-series data storage strategy.
*   **Simulation Control**: Needs a dedicated service/router in FastAPI to handle artificial stress injections and trigger the data generators.