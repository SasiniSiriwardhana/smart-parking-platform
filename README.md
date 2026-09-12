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

## 15. Future 8-Day Development Roadmap

| Day | Title | Key Objectives |
|---|---|---|
| **Day 1 (Completed)** | **Project Setup** | Django, DRF, Oracle DB, Tailwind, Spring Boot & Maven foundation. |
| **Day 2** | **Authentication & UI** | User model extensions, driver profiles, JWT / session auth, role management, dashboard UI. |
| **Day 3** | **Parking Locations & Map** | Parking garages and surface lots data model, geospatial coordinates, Leaflet/Mapbox map integration. |
| **Day 4** | **Parking Availability** | Real-time spot availability tracker, capacity thresholds, occupancy state transitions. |
| **Day 5** | **ML Availability Prediction** | Occupancy forecasting model (time-series / gradient boosting) and batch prediction pipeline. |
| **Day 6** | **Smart Recommendation & Reservation** | Spring Boot scoring algorithm (distance, rate, occupancy, walking time), slot booking, and reservation holds. |
| **Day 7** | **Parking Session, AI & Alerts** | Active parking session timers, fee calculator, automated notifications, conversational parking assistant. |
| **Day 8** | **Dashboard, Testing & Deployment**| Driver & operator analytics dashboards, end-to-end tests, Dockerization, and production deployment guide. |
