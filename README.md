# Smart Parking Availability Platform

A real-world, full-stack, distributed software platform designed to optimize urban mobility by helping drivers locate nearby parking spaces in real-time, view live availability, compare pricing and walking distances, forecast future occupancy with Machine Learning, receive intelligent multi-factor parking recommendations, and reserve parking slots seamlessly.

---

## 1. Project Description

Urban parking congestion causes significant fuel waste, traffic gridlock, and driver frustration. The **Smart Parking Availability Platform** provides an end-to-end smart mobility solution:
- **Real-Time Visibility:** Instant updates on spot vacancies across multiple parking garages and open lots.
- **Smart Recommendations:** Multi-criteria ranking powered by an independent Java Spring Boot engine evaluating distance, hourly rates, predicted vacancy, and walking duration.
- **Occupancy Forecasting:** Machine learning models forecasting vacancy rates for upcoming hours.
- **Guaranteed Reservations:** Secure booking workflows and hold timers preventing spot sniping.
- **Active Session Tracking:** In-app active parking session monitoring with automated tariff calculations.

---

## 2. Real-World Problem

Drivers in dense metropolitan areas spend an average of 15 to 20 minutes circling blocks searching for available parking, contributing to:
1. **Traffic Congestion:** Up to 30% of downtown traffic is caused by drivers hunting for parking.
2. **Economic Loss:** Thousands of dollars in wasted fuel and lost productivity per driver annually.
3. **Environmental Impact:** High carbon emissions and localized air pollution around commercial hubs.
4. **Lack of Transparent Pricing:** Inability to compare pricing, distance, and safety amenities upfront.

This platform directly addresses these challenges through intelligent discovery, transparent comparison, and automated reservations.

---

## 3. Day 1 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Main Backend** | Python 3.13 / Django 5.1 | Core application logic, routing, and administrative controls |
| **API Framework** | Django REST Framework (DRF) | RESTful API design and JSON serialization |
| **Database** | Oracle Database + python-oracledb | Enterprise transactional database management via Django ORM |
| **Recommendation Engine** | Java 21 LTS + Spring Boot 3.3.4 | Dedicated microservice for scoring & recommendation algorithms |
| **Build Tool (Java)** | Apache Maven | Build lifecycle, dependency management, and compilation |
| **Frontend Templates** | Django Templates | Server-side rendered views without unnecessary single-page bloat |
| **Styling** | Tailwind CSS | Modern, utility-first CSS design with glassmorphic aesthetics |
| **Environment Config** | python-dotenv / .env | Secure configuration isolation for credentials and parameters |

---

## 4. Project Architecture

The platform uses a distributed micro-services architecture:

```
+-------------------------------------------------------------------------+
|                              Client Layer                               |
|            Desktop & Mobile Browsers (Tailwind CSS + HTML5)             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Django 5.1 Backend (Port 8000)                         |
|   - apps.accounts: Authentication & driver profiles                     |
|   - apps.parking: Parking lots, spatial data, spots                     |
|   - apps.reservations: Booking lifecycles & holds                       |
|   - apps.sessions: Active timer & billing tracking                      |
|   - apps.core: Health checks & system utilities                         |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+-----------------------------------+  +----------------------------------+
|   Oracle Database (Port 1521)     |  | Spring Boot Engine (Port 8081)   |
|   - python-oracledb (Thin Mode)   |  | - Smart recommendation scoring   |
|   - Django ORM Entities           |  | - Multi-factor ranking engine    |
+-----------------------------------+  +----------------------------------+
```

---

## 5. Folder Structure

```
smart-parking-platform/
│
├── django_backend/
│   ├── manage.py                   # Django management utility
│   ├── requirements.txt            # Python backend dependencies
│   ├── package.json                # Tailwind CSS compilation scripts
│   ├── tailwind.config.js          # Tailwind template content scanner
│   ├── .env.example                # Sample environment variables
│   ├── .env                        # Local development settings (git-ignored)
│   ├── config/                     # Django core project configuration
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py             # Oracle DB, DRF, Apps, Static config
│   │   ├── urls.py                 # Core routing table
│   │   └── wsgi.py
│   ├── apps/                       # Modular Django business applications
│   │   ├── core/                   # Health checks & DB verification command
│   │   ├── accounts/               # User authentication & profiles
│   │   ├── parking/                # Parking lots, spots & pricing
│   │   ├── reservations/           # Slot booking & reservations
│   │   └── sessions/               # Active parking sessions (label: parking_sessions)
│   ├── templates/                  # Server-rendered HTML templates
│   │   ├── base.html               # Base layout with Tailwind, fonts, navbar
│   │   └── home.html               # Modern landing page
│   └── static/
│       └── css/
│           ├── input.css           # Tailwind source with custom styles
│           └── output.css          # Pre-compiled CSS output
│
├── recommendation_service/         # Java Spring Boot recommendation engine
│   ├── pom.xml                     # Maven project definition
│   └── src/
│       ├── main/
│       │   ├── java/com/smartparking/recommendation/
│       │   │   ├── RecommendationServiceApplication.java
│       │   │   ├── controller/     # REST controllers (Health check)
│       │   │   ├── service/        # Future recommendation algorithms
│       │   │   ├── model/          # Future DTOs and models
│       │   │   └── config/         # Spring Boot configurations
│       │   └── resources/
│       │       └── application.properties # Runs on port 8081
│       └── test/
│
├── ml/                             # Machine Learning module (Day 5)
│   └── README.md
│
├── README.md                       # Comprehensive project documentation
└── .gitignore                      # Git exclusion rules
```

---

## 6. Prerequisites

Ensure the following tools are installed on your machine:

1. **Python 3.11+** (Tested on Python 3.13)
2. **Java 17+ or 21 LTS** (Tested on Oracle / OpenJDK 21 LTS)
3. **Apache Maven 3.8+**
4. **Node.js & npm** (Optional, for re-compiling custom Tailwind classes)
5. **Oracle Database 19c, 21c, or 23ai** (Local instance, XE, or Docker container)

---

## 7. Django Setup Instructions

Navigate to the Django backend directory and create a dedicated virtual environment:

```powershell
# From the project root
cd django_backend

# 1. Create Python virtual environment
python -m venv venv

# 2. Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# (On Linux / macOS use: source venv/bin/activate)

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. Oracle Database Configuration Instructions

The project uses **`python-oracledb`** in default **Thin Mode**, meaning no separate Oracle Instant Client installation is required.

### Step 1: Prepare your `.env` File
In `django_backend/`, copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

Edit `.env` with your Oracle connection parameters:
```env
ORACLE_DB_NAME=FREEPDB1           # Pluggable database / service name
ORACLE_USER=smart_parking_user    # Oracle schema username
ORACLE_PASSWORD=YourPassword123   # Oracle user password
ORACLE_HOST=localhost             # Hostname / IP of Oracle instance
ORACLE_PORT=1521                  # Oracle TNS listener port (default: 1521)
```

### Step 2: Test Oracle Database Connectivity
Run the built-in diagnostic verification command:
```powershell
python manage.py check_db
```
- If Oracle is running and credentials are valid, you will see `[SUCCESS] Successfully connected to Oracle Database!`.
- If Oracle is not yet started, clear troubleshooting tips are displayed.

### Step 3: Run Database Migrations
Once connected to your Oracle instance:
```powershell
python manage.py migrate
```

---

## 9. Tailwind CSS Setup Instructions

Tailwind CSS comes pre-compiled in `static/css/output.css` for instant development. If you wish to build or customize the CSS:

```powershell
cd django_backend
npm install
# Rebuild CSS:
npm run build:css

# Watch for template changes continuously:
npm run watch:css
```

---

## 10. Spring Boot Setup Instructions

The recommendation engine is located in `recommendation_service/`.

```powershell
cd recommendation_service

# Build the project using Maven
mvn clean package

# Run all unit tests
mvn test
```

---

## 11. How to Run Django Backend

```powershell
cd django_backend
.\venv\Scripts\Activate.ps1

# 1. Run system integrity checks
python manage.py check

# 2. Start development server
python manage.py runserver 8000
```
Visit: **`http://127.0.0.1:8000/`** to view the landing page.

---

## 12. How to Run Spring Boot Recommendation Service

```powershell
cd recommendation_service

# Run Spring Boot application (runs on port 8081)
mvn spring-boot:run
```
Or run the packaged jar:
```powershell
java -jar target/recommendation-service-1.0.0-SNAPSHOT.jar
```

---

## 13. Health-Check API Endpoints

Both backend services expose dedicated health-check endpoints for automated monitoring and verification:

| Service | Protocol / URL | Expected Response |
|---|---|---|
| **Django Backend** | `GET http://127.0.0.1:8000/api/health/` | `{"status": "ok", "service": "django-backend"}` |
| **Spring Boot Engine** | `GET http://127.0.0.1:8081/api/recommendation/health` | `{"status": "ok", "service": "recommendation-service"}` |

---

## 14. Day 1 Completion Checklist

- [x] **Project Scaffolding:** Clean, modular repository structure.
- [x] **Django Framework:** Django 5.1 configured with modular apps (`accounts`, `parking`, `reservations`, `sessions`, `core`).
- [x] **Django Session Isolation:** App `sessions` configured with `label = 'parking_sessions'` to prevent conflicts with `django.contrib.sessions`.
- [x] **Django REST Framework:** Configured with Day 1 health endpoint at `/api/health/`.
- [x] **Oracle Database Configuration:** `django.db.backends.oracle` and `python-oracledb` configured with environment variable isolation.
- [x] **DB Verification Tool:** Custom `python manage.py check_db` diagnostic command.
- [x] **Tailwind CSS UI:** Server-rendered templates (`base.html`, `home.html`) with modern typography, glassmorphism, and responsive layout.
- [x] **Java Spring Boot:** Spring Boot 3.3.4 (Java 21 LTS) microservice configured with Maven.
- [x] **Spring Boot Health Endpoint:** REST endpoint implemented at `/api/recommendation/health`.
- [x] **Security & Environment:** Sensitive parameters isolated in `.env.example` and `.env`; secrets omitted from version control.
- [x] **Git Configuration:** Comprehensive `.gitignore` for Python, Django, Java, Maven, Node, and IDEs.

---

## 15. Day 2 Completion Checklist

- [x] **Feature Branch:** All Day 2 work isolated on `feature/day-02-authentication-ui`.
- [x] **UserProfile Model:** Extended Django `User` with `UserProfile` (role, phone, timestamps) via `OneToOneField`.
- [x] **User Roles:** `CUSTOMER` and `PARKING_PROVIDER` roles via `UserRole.TextChoices`.
- [x] **Registration:** `RegisterSerializer` + `RegisterAPIView` (POST `/api/auth/register/`) returning JWT tokens on success.
- [x] **Login:** `LoginSerializer` + `LoginAPIView` (POST `/api/auth/login/`) issuing access + refresh JWT tokens with embedded `role` claim.
- [x] **Logout:** `LogoutAPIView` (POST `/api/auth/logout/`) blacklisting refresh tokens via `simplejwt.token_blacklist`.
- [x] **JWT Token Refresh:** `TokenRefreshView` (POST `/api/auth/token/refresh/`) via `simplejwt`.
- [x] **Password Validation:** Django's built-in validators + custom `RegistrationForm` validation (strength, match, uniqueness).
- [x] **Protected Profile API:** `ProfileAPIView` (GET/PUT `/api/auth/profile/`) requires Bearer token.
- [x] **Web Registration Page:** `/register/` — Tailwind-styled form with real-time validation error display.
- [x] **Web Login Page:** `/login/` — Tailwind-styled form with `?next=` redirect support.
- [x] **Protected Dashboard:** `/dashboard/` — Role-specific UI for Customer and Parking Provider.
- [x] **User Profile Page:** `/profile/` — Editable name, phone; read-only account info.
- [x] **Logout Web View:** POST `/logout/` invalidates Django session and redirects.
- [x] **Auth-Aware Navbar:** Responsive Tailwind navbar with mobile hamburger menu; shows name/role/logout when authenticated.
- [x] **Role-Specific Dashboard:** Customer sees parking search cards; Parking Provider sees operations/analytics cards.
- [x] **Admin Integration:** `UserProfile` registered as inline in Django Admin.
- [x] **Test Suite:** 40 tests across model, API, and web view layers — all passing with SQLite test DB.
- [x] **Atomic Git Commits:** 25+ meaningful commits on `feature/day-02-authentication-ui`.

---

## 16. Day 2 Authentication API Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| `POST` | `/api/auth/register/` | No | Register a new user; returns JWT tokens |
| `POST` | `/api/auth/login/` | No | Login with email + password; returns JWT tokens |
| `POST` | `/api/auth/token/refresh/` | No (needs refresh token) | Obtain a fresh access token |
| `POST` | `/api/auth/logout/` | Yes (Bearer) | Blacklist refresh token |
| `GET` | `/api/auth/profile/` | Yes (Bearer) | Retrieve authenticated user's profile |
| `PUT` | `/api/auth/profile/` | Yes (Bearer) | Update name / phone number |

### Example: Register Request
```json
POST /api/auth/register/
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "password": "Secure@123!",
  "confirm_password": "Secure@123!",
  "role": "CUSTOMER"
}
```

### Example: Login Response
```json
{
  "message": "Login successful.",
  "user": {
    "id": 1,
    "username": "jane@example.com",
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "CUSTOMER",
    "profile": { "role": "CUSTOMER", "phone_number": "", ... }
  },
  "tokens": {
    "access": "<JWT access token>",
    "refresh": "<JWT refresh token>"
  }
}
```

---

---

## 18. Day 04 — Real-Time Parking Availability

Day 04 introduces **real-time parking slot availability** powered by **Django Channels** and **WebSockets**, allowing users to observe live occupancy changes instantly without refreshing their web browser.

### Implemented Features:

* **Individual Parking Slots:** `ParkingSlot` model linked to `ParkingLot` with designated slot identifiers (e.g. `A01`, `A02`, `B05`).
* **Available / Occupied Slot States:** `SlotStatus` choices (`AVAILABLE` 🟢 / `OCCUPIED` 🔴) with model helper methods (`occupy()`, `vacate()`, `is_available`, `is_occupied`).
* **Dynamic Occupancy & Availability Calculation:** Real-time counters ensuring `Total Slots = Occupied Slots + Available Slots` consistency at all times.
* **Django Channels & ASGI Architecture:** Full ASGI configuration routing both standard HTTP/REST requests and WebSocket streams.
* **WebSocket Availability Feed:**
  * Route: `ws://127.0.0.1:8000/ws/parking/<parking_id>/availability/`
  * Global Stream: `ws://127.0.0.1:8000/ws/parking/availability/`
* **Real-Time Broadcasting Service:** Instant dispatch of occupancy totals and slot statuses to connected channel groups when slot states change.
* **Simulated Car Entry & Exit Operations:** Backend simulation engine with edge-case validation (`Parking is full.` / `No occupied slots available.`).
* **Interactive Parking Slot Grid:** Responsive slot layout on the parking detail page displaying live color-coded cards and badges.
* **Provider Simulation Controls:** Dedicated test controls on the parking detail and provider management pages for verified owners/administrators.
* **Real-Time Parking Finder Sync:** Live card counters and map popups update dynamically across all active client browsers.
* **Automated Test Suite:** 18 dedicated Day 04 automated tests covering ORM models, status transitions, simulation constraints, REST APIs, authorization, and WebSocket communicators (87 total passing tests).

### Real-Time Availability API Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| `GET` | `/api/parking/<id>/availability/` | No | Get real-time availability and occupancy statistics |
| `GET` | `/api/parking/<id>/slots/` | No | Get list of individual parking slots and current states |
| `POST` | `/api/parking/<id>/simulate-entry/` | Provider/Admin | Simulate vehicle arrival (occupies first available slot) |
| `POST` | `/api/parking/<id>/simulate-exit/` | Provider/Admin | Simulate vehicle departure (vacates an occupied slot) |
| `POST` | `/api/parking/<id>/slots/<slot_id>/toggle/` | Provider/Admin | Toggle individual slot between Available and Occupied |

### WebSocket Protocol Example

**Connect:**
```
ws://127.0.0.1:8000/ws/parking/1/availability/
```

**Initial Snapshot Payload:**
```json
{
  "type": "availability_snapshot",
  "data": {
    "parking_id": 1,
    "name": "Central Plaza Parking",
    "total_slots": 100,
    "occupied_slots": 73,
    "available_slots": 27,
    "occupancy_percentage": 73.0,
    "is_full": false,
    "is_available": true,
    "is_open_now": true,
    "slots": [
      {"id": 1, "slot_number": "A01", "status": "OCCUPIED", "is_available": false},
      {"id": 2, "slot_number": "A02", "status": "AVAILABLE", "is_available": true}
    ]
  }
}
```

### Current Implementation & Sensor Simulation

The platform currently utilizes a **backend simulation mechanism** (`Simulate Car Entry` / `Simulate Car Exit`) because physical IoT parking sensors are not yet deployed in the test environment.

### Future Enhancement

In future stages, physical IoT-based ultrasonic/magnetic parking sensors or camera-based license plate recognition (ANPR) systems can connect to the platform's REST endpoints or ingestion pipelines to deliver hardware-measured occupancy streams in real time.

---

## 20. Day 05 — Machine Learning Availability Prediction (Portfolio Feature)

Day 05 introduces the platform's main intelligent predictive capability: **ML-based Parking Availability Prediction**. The system analyzes historical occupancy patterns, time-of-day dynamics, day-of-week trends, turnover rates, and environmental factors (events, holidays) to forecast available spaces in **approximately 20 minutes**.

### 🌟 End-to-End Prediction Flow
```
Real-Time Parking State (Live DB / WebSockets)
                      ↓
  Contextual Features (Time, Day, Event, Holiday)
                      ↓
  Pretrained RandomForestRegressor Pipeline
                      ↓
  Future Forecast & Uncertainty Interval (~20 min)
                      ↓
  Explainable Confidence & Capacity Warning Alerts
                      ↓
  Real-Time Dynamic UI (Parking Details Card)
```

### 📊 Dataset Schema & Synthetic Status
> **Important Note:** The current training dataset is **synthetic historical parking data for development and model training**. In production environments, this dataset can be substituted with recorded IoT sensor telemetry or ticketing histories.

- **Dataset Size:** 4,800 historical records across diverse facility archetypes (commercial, transit, retail, office, mixed).
- **Required Columns:**
  - `Date`, `Day`, `Time`, `Parking Lot`, `Total Slots`, `Occupied Slots`, `Available Slots`, `Average Parking Duration`, `Nearby Event`, `Holiday`, `Future Available Slots`
- **Data Integrity Constraints:**
  - $0 \le \text{Occupied Slots} \le \text{Total Slots}$
  - $\text{Available Slots} = \text{Total Slots} - \text{Occupied Slots}$
  - $0 \le \text{Future Available Slots} \le \text{Total Slots}$

### 🧠 Model Architecture & Hyperparameters
- **Model:** `RandomForestRegressor`
- **Preprocessing:** Scikit-learn `ColumnTransformer` with `OneHotEncoder` (categorical `Parking Lot`, `Day`) and `StandardScaler` (numerical occupancy metrics, cyclical $\sin/\cos$ time encodings, binary flags).
- **Hyperparameters:**
  ```python
  {
      "n_estimators": 100,
      "max_depth": 15,
      "min_samples_split": 5,
      "min_samples_leaf": 2,
      "random_state": 42,
      "n_jobs": -1
  }
  ```
- **Serialization:** Persisted as `ml/models/parking_availability_model.joblib` using `joblib` and cached in-memory for zero disk I/O inference.

### 📈 Actual Model Evaluation Metrics
Evaluated on a held-out 20% test partition (960 validation samples):
- **Mean Absolute Error (MAE):** **2.86 spaces**
- **Root Mean Squared Error (RMSE):** **3.88 spaces**
- **$R^2$ Score:** **0.9902**
- **Max Observed Error:** **26.33 spaces**

### 🔮 Prediction Interval, Confidence & Warnings
- **Prediction Horizon:** Target timestamp = $\text{Current Time} + 20\text{ minutes}$.
- **Uncertainty Range:** Computed via model validation error:
  $$\text{margin} = \max(1, \text{round}(\text{RMSE} \times 0.75))$$
  $$\text{Range} = [\max(0, \text{Pred} - \text{margin}),\, \min(\text{Total}, \text{Pred} + \text{margin})]$$
- **Explainable Confidence Score:**
  - $\text{RMSE} / \text{Total Capacity} \le 6\% \implies$ **High**
  - $\text{RMSE} / \text{Total Capacity} \le 12\% \implies$ **Medium**
  - $\text{RMSE} / \text{Total Capacity} > 12\% \implies$ **Low**
- **Capacity Warning Rules:**
  - $\le 10\%$ predicted available $\implies$ 🔴 *Parking is likely to become full soon.*
  - $\le 25\%$ predicted available $\implies$ 🟡 *Parking availability may become limited.*
  - $> 25\%$ predicted available $\implies$ 🟢 *Parking availability is expected to remain available.*

### 🚀 Management Commands & Usage
```bash
# 1. Train and serialize ML model:
python manage.py train_parking_model

# 2. Predict availability for a parking lot by ID:
python manage.py predict_parking_availability --parking-id 1

# 3. Predict availability interactively / standalone:
python manage.py predict_parking_availability --name "Parking A" --total-slots 100 --occupied-slots 92
```

### 📡 API Reference
| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/api/parking/<id>/prediction/` | Generates 20-minute availability forecast with confidence, range, warning level, and explainability factors. |

---

## 21. 8-Day Development Roadmap

| Day | Title | Status | Key Objectives |
|---|---|---|---|
| **Day 1** | **Project Setup** | ✅ Completed | Django, DRF, Oracle DB, Tailwind, Spring Boot & Maven foundation. |
| **Day 2** | **Authentication & UI** | ✅ Completed | UserProfile, JWT auth, registration/login/logout, protected routes, role dashboards, 40 tests. |
| **Day 3** | **Parking Locations & Map** | ✅ Completed | Parking garages & surface lots model, geospatial coordinates, Leaflet map, distance filters. |
| **Day 4** | **Real-Time Parking Availability** | ✅ Completed | ParkingSlot model, Django Channels, WebSockets, simulated car entry/exit, live slot grid, 87 total tests. |
| **Day 5** | **ML Availability Prediction** | ✅ Completed | RandomForestRegressor, 20-min forecasting, uncertainty range, confidence, capacity warnings, API & UI. |
| **Day 6** | **Smart Recommendation & Reservation** | ⏳ Planned | Spring Boot scoring algorithm (distance, rate, occupancy, walking time), slot booking, and reservation holds. |
| **Day 7** | **Parking Session, AI & Alerts** | ⏳ Planned | Active parking session timers, fee calculator, automated notifications, conversational parking assistant. |
| **Day 8** | **Dashboard, Testing & Deployment**| ⏳ Planned | Driver & operator analytics dashboards, end-to-end tests, Dockerization, and production deployment guide. |


