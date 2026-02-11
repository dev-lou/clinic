# 📘 ISUFST CareHub - Complete System Documentation

**A Modern Healthcare Management Platform for University Clinics**

*Capstone Project 2026 - Technical Documentation*

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Core Features & Modules](#core-features--modules)
6. [Database Schema](#database-schema)
7. [API Documentation](#api-documentation)
8. [User Roles & Permissions](#user-roles--permissions)
9. [Installation & Deployment](#installation--deployment)
10. [User Workflows](#user-workflows)
11. [Security & Compliance](#security--compliance)
12. [Testing & Quality Assurance](#testing--quality-assurance)
13. [Future Enhancements](#future-enhancements)
14. [Troubleshooting](#troubleshooting)
15. [References & Credits](#references--credits)

---

## 1. Executive Summary

### 1.1 Project Vision

ISUFST CareHub is a comprehensive digital healthcare management system designed specifically for university clinic operations. It transforms traditional paper-based clinic workflows into a modern, efficient, and integrated digital platform.

### 1.2 Problem Statement

Traditional university clinics face several challenges:
- Manual appointment scheduling leading to long wait times
- Disconnected medicine inventory and reservation systems
- Paper-based health records that are difficult to track
- No real-time queue management
- Limited analytics for clinic operations
- Lack of digital communication with students

### 1.3 Solution

CareHub provides an end-to-end integrated solution featuring:
- **Intelligent Appointment System** - Real-time slot availability with automatic doctor assignment
- **Queue Management** - Live queue display with WebSocket updates
- **Medicine Reservation** - Online reservation with QR code pickup
- **Health Timeline** - Unified patient dashboard with complete medical history
- **AI-Powered Symptom Screening** - Pre-appointment health assessment
- **Analytics Dashboard** - Comprehensive reporting for decision-making
- **Multi-Channel Notifications** - Email, SMS, and in-app alerts

### 1.4 Key Metrics

| Metric | Value |
|--------|-------|
| Total Modules | 13 Blueprints |
| Database Tables | 20+ Tables |
| API Endpoints | 15+ REST APIs |
| User Roles | 4 (Student, Nurse, Doctor, Admin) |
| Templates | 25+ HTML Pages |
| Real-time Features | WebSocket Queue Display |
| External Integrations | 3 (Gemini AI, Semaphore SMS, Gmail SMTP) |

---

## 2. System Overview

### 2.1 System Purpose

CareHub serves as the central digital hub for all clinic operations at Iloilo State University of Fisheries Science and Technology (ISUFST), providing:

1. **For Students:**
   - Self-service appointment booking
   - Medicine reservation and tracking
   - Digital health records access
   - Real-time queue status

2. **For Clinic Staff:**
   - Efficient patient queue management
   - Digital medical records
   - Inventory tracking
   - Automated notifications

3. **For Administrators:**
   - Comprehensive analytics
   - Resource scheduling
   - Audit logging
   - System configuration

### 2.2 System Scope

**Included:**
- Appointment booking and management
- Medicine inventory and reservation system
- Clinic queue management
- Digital logbook (check-in/check-out)
- Health records and visit history
- Prescription management
- Doctor scheduling and assignment
- Analytics and reporting
- Notification system (Email/SMS)
- QR code check-in system
- AI-powered symptom screening
- Health certificate generation

**Excluded (Future Phases):**
- Telemedicine video consultations
- Laboratory test management
- Pharmacy sales/billing system
- Insurance claim processing

### 2.3 Target Users

- **Primary Users:** ISUFST Students (500+ registered users)
- **Secondary Users:** Clinic Staff (Nurses, Doctors, Admin)
- **System Administrators:** IT Staff

---

## 3. Technology Stack

### 3.1 Backend Technologies

#### Core Framework
```
Flask 3.0.0          - Lightweight Python web framework
Python 3.11+         - Programming language
```

#### Flask Extensions
```
Flask-Login          - User session management
Flask-SQLAlchemy     - ORM for database operations
Flask-WTF            - Form handling & CSRF protection
Flask-SocketIO       - WebSocket support for real-time features
Flask-Migrate        - Database schema migrations
Werkzeug             - WSGI utilities & password hashing
```

#### Database
```
Turso (LibSQL)       - Distributed SQLite (Production)
SQLite               - Local development database
SQLAlchemy           - Database ORM layer
```

#### External Services
```
Google Gemini AI     - Chatbot & symptom screening
Semaphore API        - Philippine SMS notifications
Gmail SMTP           - Email notifications
```

#### Utilities
```
QRCode               - QR code generation
ReportLab            - PDF generation for certificates
APScheduler          - Background job scheduling
python-dotenv        - Environment variable management
secrets              - Secure token generation
```

### 3.2 Frontend Technologies

#### CSS Framework
```
Tailwind CSS 3.x     - Utility-first CSS framework
Font Awesome 6.0     - Icon library
Google Fonts         - Inter & Plus Jakarta Sans typography
```

#### JavaScript Libraries
```
Vanilla JavaScript   - Native DOM manipulation
Socket.IO Client     - Real-time WebSocket connection
Chart.js 4.4.0       - Data visualization
SweetAlert2          - Beautiful alert/modal popups
HTML5-QRCode         - QR code scanner library
```

#### Build Tools
```
npm/Node.js          - Package manager
Tailwind CLI         - CSS compilation
PostCSS              - CSS processing
```

### 3.3 Development Tools

```
Git                  - Version control
VS Code              - Code editor
Flask CLI            - Command-line interface
Python venv          - Virtual environment
```

### 3.4 Deployment Stack

```
Render.com           - Cloud hosting platform
Gunicorn             - WSGI HTTP server
```

---

## 4. System Architecture

### 4.1 Architecture Pattern

**Modular Blueprint Architecture (MVC Pattern)**

```
┌─────────────────────────────────────────────┐
│          Flask Application Factory          │
│                  (app.py)                   │
└─────────────────────────────────────────────┘
                      │
      ┌───────────────┴───────────────┐
      │                               │
┌─────▼──────┐                 ┌──────▼──────┐
│ Blueprints │                 │   Models    │
│  (Routes)  │◄───────────────►│ (Database)  │
└─────┬──────┘                 └──────┬──────┘
      │                               │
┌─────▼──────────────────────────────▼──────┐
│            Templates (Views)              │
│         Jinja2 HTML Rendering             │
└───────────────────────────────────────────┘
```

### 4.2 Blueprint Structure

The system is divided into 13 independent blueprints:

| Blueprint | Purpose | URL Prefix |
|-----------|---------|------------|
| auth.py | Authentication & user management | `/auth` |
| appointments.py | Appointment booking & management | `/appointments` |
| reservations.py | Medicine reservation system | `/reservations` |
| inventory.py | Medicine inventory management | `/inventory` |
| clinic_queue.py | Queue management system | `/queue` |
| logbook.py | Digital clinic logbook | `/logbook` |
| notifications.py | Notification management | `/notifications` |
| patient_dashboard.py | Patient health timeline | `/dashboard` |
| analytics.py | Analytics & reporting | `/analytics` |
| api.py | REST API for mobile apps | `/api/v1` |
| queue_display.py | Real-time queue display board | `/queue-display` |
| search.py | Global search functionality | `/search` |
| symptom_screening.py | AI symptom checker | `/screening` |
| chatbot.py | AI health assistant | `/chatbot` |

### 4.3 Data Flow

```
┌──────────┐      HTTP       ┌──────────┐
│  Client  │ ◄────────────► │  Flask   │
│(Browser) │                 │Blueprint │
└──────────┘                 └────┬─────┘
                                  │
                            ┌─────▼─────┐
                            │SQLAlchemy │
                            │    ORM    │
                            └─────┬─────┘
                                  │
                            ┌─────▼─────┐
                            │   Turso   │
                            │ Database  │
                            └───────────┘
```

### 4.4 Real-Time Architecture

```
┌──────────┐   Socket.IO    ┌──────────┐
│  Client  │ ◄────────────► │  Flask   │
│(Browser) │   WebSocket    │ SocketIO │
└──────────┘                └────┬─────┘
                                 │
                           ┌─────▼─────┐
                           │   Queue   │
                           │  Events   │
                           └───────────┘
```

### 4.5 File Structure

```
clinic/
├── app.py                          # Application factory
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies
├── tailwind.config.js              # Tailwind configuration
│
├── Blueprints (Business Logic)
│   ├── auth.py                     # Authentication
│   ├── appointments.py             # Appointments
│   ├── reservations.py             # Medicine reservations
│   ├── inventory.py                # Inventory management
│   ├── clinic_queue.py             # Queue system
│   ├── logbook.py                  # Clinic logbook
│   ├── notifications.py           # Notifications
│   ├── patient_dashboard.py        # Patient portal
│   ├── analytics.py                # Analytics dashboard
│   ├── api.py                      # REST API
│   ├── queue_display.py            # Queue display board
│   ├── search.py                   # Search functionality
│   ├── symptom_screening.py        # Symptom checker
│   └── chatbot.py                  # AI chatbot
│
├── Models (Database)
│   ├── models.py                   # Core models
│   └── models_extended.py          # Extended models
│
├── Utilities
│   ├── advanced_utils.py           # QR, PDF generation
│   ├── notification_service.py     # Email/SMS service
│   ├── scheduler.py                # Background jobs
│   └── rbac.py                     # Role-based access control
│
├── templates/                      # HTML templates (25+ files)
│   ├── admin_base.html             # Admin layout
│   ├── student_base.html           # Student layout
│   ├── index.html                  # Homepage
│   ├── login.html                  # Login page
│   ├── register.html               # Registration
│   ├── book_appointment.html       # Appointment booking
│   ├── my_appointments.html        # Student appointments
│   ├── medicines.html              # Medicine catalog
│   ├── my_reservations.html        # Student reservations
│   ├── patient_dashboard.html      # Health timeline
│   ├── analytics_dashboard.html    # Analytics
│   ├── admin_logbook.html          # Logbook with QR scanner
│   └── ...                         # (20+ more templates)
│
├── static/                         # Static assets
│   ├── css/
│   │   ├── output.css              # Compiled Tailwind
│   │   ├── animations.css          # Custom animations
│   │   └── fontawesome.min.css     # Icons
│   ├── js/
│   │   └── calendar.js             # Calendar widget
│   ├── images/                     # Photos, logos
│   └── favicon.ico
│
└── Documentation
    ├── README_QUICKSTART.md        # Quick start guide
    ├── ENHANCEMENTS.md             # Feature documentation
    ├── IMPLEMENTATION_REPORT.md    # Implementation details
    └── NAVIGATION_GUIDE.md         # Feature navigation
```

---

## 5. Core Features & Modules

### 5.1 Authentication & Authorization

**File:** `auth.py`

**Features:**
- User registration with email verification
- Secure login with password hashing (Werkzeug)
- Session management (Flask-Login)
- Role-based access control (RBAC)
- User profile management

**Routes:**
- `GET/POST /auth/login` - User login
- `GET/POST /auth/register` - Student registration
- `GET /auth/logout` - Logout
- `GET/POST /auth/profile` - Profile management
- `GET /auth/users` - User list (admin only)
- `POST /auth/users/<id>/edit` - Edit user (admin only)

**Security Features:**
- Password hashing with `generate_password_hash()`
- CSRF protection on all forms
- Session timeout
- Role verification decorators

---

### 5.2 Appointment System

**File:** `appointments.py`

**Core Functionality:**

1. **Intelligent Slot Management**
   - Dynamic time slot generation (9 AM - 5 PM, 30-min intervals)
   - Real-time availability checking
   - Service-specific capacity limits (Medical: 3/slot, Dental: 2/slot)
   - Past slot prevention

2. **Automatic Doctor Assignment**
   - Auto-assign first available doctor on booking
   - Support for manual reassignment by admin
   - Doctor specialization matching (Medical/Dental)

3. **QR Code Check-In**
   - Secure token generation on booking
   - QR code with ISUFST logo branding
   - 30-day validity period
   - API verification endpoint

**Routes:**
- `GET /appointments/book` - Booking page
- `POST /appointments/book` - Submit booking
- `GET /appointments/my` - Student's appointments
- `GET /appointments/admin` - Admin appointments list (staff only)
- `POST /appointments/admin/<id>/update-status` - Update status (staff)
- `POST /appointments/admin/<id>/assign-doctor` - Assign doctor (staff)
- `GET /appointments/api/get-qr/<id>` - Get QR code image
- `POST /appointments/api/verify-qr` - Verify QR for check-in (staff)
- `GET /appointments/check-availability` - Check date availability (AJAX)

**Database Tables:**
- `appointments` - Core appointment data
- `appointment_extended` - Extended data (assigned doctor, QR token)
- `appointment_waitlist` - Overflow waitlist management

**Workflow:**
```
Student Books → System Checks Availability → Auto-Assign Doctor 
→ Generate QR Code → Send Confirmation Email → Add to Queue on Appointment Day
```

---

### 5.3 Medicine Reservation System

**File:** `reservations.py`

**Features:**

1. **Public Medicine Catalog**
   - Browse available medicines without login
   - Search and filter by name/category
   - Stock level indicators
   - Expiry date warnings

2. **Online Reservation**
   - Quantity selection with stock validation
   - QR code for pickup
   - Reservation status tracking (Reserved → Ready → Picked Up → Cancelled)
   - Expiry mechanism (auto-cancel after 7 days)

3. **Inventory Integration**
   - Atomic stock locking on reservation
   - Auto-deduction on pickup
   - Low stock alerts

**Routes:**
- `GET /reservations/medicines` - Public medicine catalog
- `POST /reservations/reserve/<medicine_id>` - Reserve medicine (authenticated)
- `GET /reservations/my` - Student's reservations
- `GET /reservations/api/get-qr/<id>` - Get reservation QR code
- `POST /reservations/api/verify-qr` - Verify QR for pickup (staff)

**Database Tables:**
- `medicine_reservations` - Core reservation data
- `medicine_reservation_extended` - Extended data (QR token)
- `inventory_locks` - Atomic stock locking (prevents over-reservation)

**Workflow:**
```
Student Reserves → Check Stock → Lock Quantity → Generate QR 
→ Email Notification → Staff Marks Ready → Student Picks Up → Update Inventory
```

---

### 5.4 Inventory Management

**File:** `inventory.py`

**Features:**
- Medicine CRUD operations (Create, Read, Update, Delete)
- Stock level tracking
- Expiry date monitoring
- Low stock alerts (< 10 units)
- Batch number tracking
- Category management

**Routes:**
- `GET /inventory/` - Inventory list (staff only)
- `POST /inventory/add` - Add new medicine (staff only)
- `POST /inventory/<id>/edit` - Edit medicine (staff only)
- `POST /inventory/<id>/delete` - Delete medicine (admin only)

**Automated Alerts:**
- Weekly expiry notifications (via `scheduler.py`)
- Low stock dashboard warnings

---

### 5.5 Queue Management System

**File:** `clinic_queue.py`

**Features:**

1. **Queue Operations**
   - Manual add to queue (staff)
   - Auto-enqueue from confirmed appointments
   - Priority levels (Emergency, Appointment, Walk-in)
   - Queue position tracking
   - Estimated wait time calculation

2. **Staff Controls**
   - Call next patient
   - Mark as "now serving"
   - Complete queue entry
   - Remove from queue

**Routes:**
- `GET /queue/` - Queue management dashboard (staff only)
- `POST /queue/add` - Add patient to queue (staff)
- `POST /queue/<id>/call` - Call next patient (staff)
- `POST /queue/<id>/complete` - Complete entry (staff)

**Database Table:**
- `queue` (status: Waiting, In Progress, Completed)

---

### 5.6 Real-Time Queue Display

**File:** `queue_display.py`

**Technology:** Flask-SocketIO (WebSocket)

**Features:**
- TV-friendly display board
- Live updates on queue changes (no page refresh)
- Now serving indicator
- Queue position for waiting patients
- Estimated wait time

**Routes:**
- `GET /queue-display/` - Public queue display page

**WebSocket Events:**
- `connect` - Client connects
- `disconnect` - Client disconnects
- `queue_update` - Broadcast queue change to all clients

**Usage:**
Display on TV/monitor at clinic entrance for students to see queue status in real-time.

---

### 5.7 Digital Clinic Logbook

**File:** `logbook.py`

**Features:**

1. **QR Code Check-In**
   - Two-tab scanner (Camera + Manual Input)
   - Live camera scanning with HTML5-QRCode library
   - Auto-populate student info from appointment QR
   - Auto-populate medicine pickup from reservation QR

2. **Manual Check-In**
   - Student search with autocomplete
   - Purpose selection (Medical, Dental, Medicine Pickup, Walk-in)
   - Notes field

3. **Check-Out Tracking**
   - Time spent calculation
   - Visit summary

**Routes:**
- `GET /logbook/` - Logbook dashboard (staff only)
- `POST /logbook/check-in` - Check-in patient (staff)
- `POST /logbook/check-out` - Check-out patient (staff)
- `GET /logbook/admin/search-students` - Student autocomplete API (staff)

**Database Table:**
- `logbook_entries` (check_in_time, check_out_time, purpose, notes)

**Workflow:**
```
Student Arrives → Staff Scans QR (or Manual Entry) → System Verifies 
→ Pre-fills Student Info → Staff Clicks Check-In → Entry Logged
→ After Consultation → Staff Clicks Check-Out → Calculate Time Spent
```

---

### 5.8 Patient Health Dashboard

**File:** `patient_dashboard.py`

**Features:**

1. **Unified Timeline View**
   - Chronological health events
   - Appointments (upcoming & past)
   - Clinic visits with diagnoses
   - Medicine reservations
   - Health certificates

2. **Health Statistics**
   - Total visits count
   - Total appointments
   - Active reservations
   - Health score indicators

3. **Quick Actions**
   - Book new appointment
   - Reserve medicine
   - View notifications
   - Submit feedback

**Routes:**
- `GET /dashboard/` - Main dashboard
- `GET /dashboard/timeline` - Timeline view
- `GET /dashboard/health-stats` - Health statistics page

**Database Integration:**
Aggregates data from:
- `appointments`
- `clinic_visits`
- `medicine_reservations`
- `health_certificates`
- `visit_feedback`

---

### 5.9 Analytics & Reporting

**File:** `analytics.py`

**Features:**

1. **Overview Statistics**
   - Today's appointments
   - Completed visits
   - Active reservations
   - Average satisfaction rating

2. **Time Series Charts**
   - Appointment trends (daily/weekly/monthly)
   - Satisfaction ratings over time
   - Service type distribution (pie chart)

3. **Operational Analytics**
   - Peak hours heatmap (busiest clinic times)
   - Doctor workload balance
   - No-show rate tracking
   - Inventory consumption patterns

4. **Demographics**
   - Student distribution by course
   - Year level breakdown
   - Common diagnoses

**Routes:**
- `GET /analytics/` - Analytics dashboard (admin/staff only)
- `GET /analytics/api/overview` - Overview stats JSON
- `GET /analytics/api/appointments-trend` - Trend data
- `GET /analytics/api/service-distribution` - Service breakdown
- `GET /analytics/api/peak-hours` - Peak hours data
- `GET /analytics/api/satisfaction-trend` - Satisfaction data
- `GET /analytics/api/doctor-workload` - Workload data
- `GET /analytics/api/no-show-rate` - No-show statistics
- `GET /analytics/api/inventory-consumption` - Medicine usage

**Visualization:** Chart.js library for interactive graphs

---

### 5.10 Symptom Screening System

**File:** `symptom_screening.py`

**Technology:** Google Gemini AI

**Features:**

1. **Interactive Symptom Checker**
   - Multi-category symptom selection
   - Severity input
   - Duration tracking
   - Additional notes

2. **AI-Powered Recommendations**
   - Service type suggestion (Medical/Dental/Emergency)
   - Urgency level assessment
   - Pre-filled appointment booking

3. **Data Collection**
   - Stores screening results for analytics
   - Links to appointments if booked

**Routes:**
- `GET /screening/` - Symptom checker page
- `POST /screening/api/screen` - Submit symptoms for AI analysis
- `GET /screening/api/symptom-categories` - Get symptom categories

**Database Table:**
- `symptom_screenings` (symptoms, analysis, recommended_service, urgency)

**Workflow:**
```
Student Describes Symptoms → AI Analyzes → Recommends Service Type 
→ Student Books Appointment → Pre-filled with Screening Data
```

---

### 5.11 AI Health Chatbot

**File:** `chatbot.py`

**Technology:** Google Gemini AI API

**Features:**
- General health advice (non-diagnostic)
- CareHub system help
- Clinic hours and services information
- First aid guidance
- Disclaimers for serious symptoms

**Routes:**
- `POST /chatbot/api/chat` - Submit chat message, get AI response

**System Prompt:**
```
You are CareHub Assistant, a friendly health advisor for ISUFST students.
Provide general health advice, but always remind users to visit the clinic 
for professional diagnosis. You can answer questions about:
- Common health concerns (fever, headache, first aid)
- How to use CareHub (booking appointments, reserving medicines)
- ISUFST clinic services and hours
```

**Integration:** Embedded chat widget on student pages

---

### 5.12 Notification System

**File:** `notification_service.py`

**Multi-Channel Notifications:**

1. **Email (SMTP)**
   - Appointment confirmation
   - 24-hour reminder
   - Cancellation notices
   - Medicine ready for pickup
   - Weekly expiry alerts (staff)

2. **SMS (Semaphore API - Philippines)**
   - Appointment reminders
   - Urgent notifications
   - Waitlist slot available

3. **In-App Notifications**
   - Real-time bell icon updates
   - Notification center page
   - Read/unread tracking

**Database Table:**
- `notifications` (user_id, title, message, type, is_read, created_at)

**Trigger Points:**
- Appointment booked → Email + SMS
- 24 hours before appointment → Reminder email
- Medicine reservation ready → Email notification
- Waitlist slot opens → SMS alert
- System announcements → In-app notification

---

### 5.13 Search System

**File:** `search.py`

**Features:**
- Global search across all entities
- Filtered search by category:
  - Students (name, email, student number)
  - Appointments (date, service type, status)
  - Visits (diagnosis, date range)
  - Medicines (name, category, stock level)

**Routes:**
- `GET /search/` - Search interface (staff only)
- `GET /search/api/students` - Search students
- `GET /search/api/appointments` - Search appointments
- `GET /search/api/visits` - Search visits
- `GET /search/api/inventory` - Search medicines

**Use Case:** Staff quickly finding patient records during consultations

---

### 5.14 REST API (Mobile Apps)

**File:** `api.py`

**Base Path:** `/api/v1/`

**Authentication:** Token-based (Bearer token in Authorization header)

**Endpoints:**

**Auth:**
- `POST /api/v1/auth/login` - Login, get token
- `GET /api/v1/auth/me` - Get current user info

**Appointments:**
- `GET /api/v1/appointments` - List appointments
- `GET /api/v1/appointments/<id>` - Get appointment details
- `POST /api/v1/appointments` - Book appointment
- `POST /api/v1/appointments/<id>/cancel` - Cancel appointment
- `GET /api/v1/appointments/availability` - Check slot availability

**Medical Records:**
- `GET /api/v1/medical-records` - Get visit history

**Medicines:**
- `GET /api/v1/medicines` - List available medicines
- `GET /api/v1/reservations` - List user's reservations
- `POST /api/v1/reservations` - Reserve medicine

**Notifications:**
- `GET /api/v1/notifications` - Get notifications
- `POST /api/v1/notifications/<id>/read` - Mark as read

**Feedback:**
- `POST /api/v1/feedback` - Submit visit feedback

**Health Summary:**
- `GET /api/v1/health-summary` - Get comprehensive health data

**Response Format:**
```json
{
  "success": true,
  "data": { },
  "message": "Operation successful"
}
```

**Error Format:**
```json
{
  "error": "Error message",
  "code": 400
}
```

**Future Use:** React Native / Flutter mobile app development

---

## 6. Database Schema

### 6.1 Core Tables

#### users

```
users
├── id (PK)
├── email (unique)
├── password_hash
├── first_name
├── last_name
├── role (enum: student, nurse, doctor, admin)
├── is_active (boolean)
├── created_at
└── updated_at
```

#### student_profiles

```
student_profiles
├── id (PK)
├── user_id (FK → users)
├── student_number (unique)
├── course
├── year_level
├── contact_number
├── emergency_contact
├── blood_type
└── allergies (text)
```

#### appointments

```
appointments
├── id (PK)
├── student_id (FK → users)
├── service_type (enum: Medical, Dental, Mental Health, etc.)
├── appointment_date
├── start_time
├── end_time
├── status (enum: Pending, Confirmed, Completed, Cancelled, No-Show)
├── reason (text)
├── created_at
└── updated_at
```

#### appointment_extended

```
appointment_extended
├── id (PK)
├── appointment_id (FK → appointments, unique)
├── assigned_doctor_id (FK → users) — Auto-assigned
├── qr_code (text) — Secure token for check-in
├── notes (text)
└── created_at
```

#### clinic_visits

```
clinic_visits
├── id (PK)
├── student_id (FK → users)
├── appointment_id (FK → appointments, nullable)
├── visit_date
├── chief_complaint (text)
├── vital_signs (JSON: temperature, bp, pulse, weight, height)
├── diagnosis (text)
├── treatment (text)
├── prescribed_medicines (text) — Linked to prescriptions
├── status (enum: Pending, Completed)
├── attended_by (FK → users) — Nurse/doctor who handled
└── created_at
```

#### inventory

```
inventory
├── id (PK)
├── medicine_name
├── category
├── quantity
├── unit (enum: tablets, bottles, sachets, etc.)
├── expiry_date
├── batch_number
├── created_at
└── updated_at
```

#### medicine_reservations

```
medicine_reservations
├── id (PK)
├── student_id (FK → users)
├── medicine_id (FK → inventory)
├── medicine_name (denormalized for history)
├── quantity
├── status (enum: Reserved, Ready, Picked Up, Cancelled, Expired)
├── reserved_at
├── picked_up_at (nullable)
└── notes (text)
```

#### medicine_reservation_extended

```
medicine_reservation_extended
├── id (PK)
├── reservation_id (FK → medicine_reservations, unique)
├── qr_code (text) — Secure token for pickup
└── created_at
```

#### queue

```
queue
├── id (PK)
├── student_id (FK → users)
├── appointment_id (FK → appointments, nullable)
├── queue_number (auto-increment per day)
├── priority (enum: Emergency, Appointment, Walk-in)
├── status (enum: Waiting, In Progress, Completed)
├── called_at (nullable)
├── completed_at (nullable)
└── created_at
```

#### logbook_entries

```
logbook_entries
├── id (PK)
├── student_id (FK → users)
├── appointment_id (FK → appointments, nullable)
├── purpose (enum: Medical, Dental, Medicine Pickup, Walk-in)
├── check_in_time
├── check_out_time (nullable)
├── notes (text)
└── created_at
```

#### notifications

```
notifications
├── id (PK)
├── user_id (FK → users)
├── title
├── message (text)
├── type (enum: appointment, reservation, system, alert)
├── is_read (boolean, default: False)
├── link (url, nullable)
└── created_at
```

### 6.2 Extended Tables

#### doctor_schedules

```
doctor_schedules
├── id (PK)
├── doctor_id (FK → users)
├── day_of_week (enum: Monday-Sunday)
├── start_time
├── end_time
├── specialization (enum: General Medicine, Dental)
├── is_active (boolean)
└── created_at
```

#### doctor_leaves

```
doctor_leaves
├── id (PK)
├── doctor_id (FK → users)
├── leave_date
├── reason (text)
└── created_at
```

#### appointment_waitlist

```
appointment_waitlist
├── id (PK)
├── student_id (FK → users)
├── service_type
├── preferred_date
├── preferred_time
├── status (enum: Waiting, Notified, Booked, Expired)
├── notified_at (nullable)
└── created_at
```

#### prescriptions

```
prescriptions
├── id (PK)
├── visit_id (FK → clinic_visits)
├── prescribed_by (FK → users) — Doctor
├── prescription_number (unique)
├── status (enum: Pending, Dispensed)
├── dispensed_at (nullable)
├── dispensed_by (FK → users, nullable) — Pharmacist/nurse
└── created_at
```

#### prescription_items

```
prescription_items
├── id (PK)
├── prescription_id (FK → prescriptions)
├── medicine_id (FK → inventory)
├── quantity
├── dosage (text, e.g., "1 tab 3x daily")
└── created_at
```

#### visit_feedback

```
visit_feedback
├── id (PK)
├── visit_id (FK → clinic_visits)
├── student_id (FK → users)
├── rating (integer, 1-5)
├── wait_time_rating (integer, 1-5)
├── staff_rating (integer, 1-5)
├── facility_rating (integer, 1-5)
├── comments (text)
├── is_anonymous (boolean)
└── submitted_at
```

#### symptom_screenings

```
symptom_screenings
├── id (PK)
├── student_id (FK → users)
├── symptoms (JSON array)
├── additional_info (text)
├── ai_analysis (text) — Gemini response
├── recommended_service (enum: Medical, Dental, Emergency)
├── urgency (enum: Low, Medium, High)
├── appointment_id (FK → appointments, nullable) — If booked
└── screened_at
```

#### audit_logs

```
audit_logs
├── id (PK)
├── user_id (FK → users)
├── action (enum: LOGIN, CREATE, UPDATE, DELETE, ACCESS)
├── entity_type (e.g., "Appointment", "User", "Inventory")
├── entity_id
├── old_value (JSON)
├── new_value (JSON)
├── ip_address
└── created_at
```

#### health_certificates

```
health_certificates
├── id (PK)
├── student_id (FK → users)
├── visit_id (FK → clinic_visits, nullable)
├── certificate_number (unique)
├── purpose (text)
├── issued_by (FK → users) — Doctor
├── issued_at
├── valid_until
└── pdf_path (file path)
```

### 6.3 Database Relationships

```
users (1) ───< (∞) appointments
users (1) ───< (∞) clinic_visits
users (1) ───< (∞) medicine_reservations
users (1) ───< (∞) queue
users (1) ───< (∞) notifications

appointments (1) ───< (1) appointment_extended
appointments (1) ───< (∞) clinic_visits (nullable)
appointments (1) ───< (∞) queue (nullable)

clinic_visits (1) ───< (∞) prescriptions
prescriptions (1) ───< (∞) prescription_items

inventory (1) ───< (∞) medicine_reservations
inventory (1) ───< (∞) prescription_items

medicine_reservations (1) ───< (1) medicine_reservation_extended
```

### 6.4 Database Indexing

For optimal performance, indexes are created on:
- `users.email` (unique)
- `student_profiles.student_number` (unique)
- `appointments.student_id`
- `appointments.appointment_date`
- `clinic_visits.student_id`
- `medicine_reservations.student_id`
- `queue.created_at`

---

## 7. API Documentation

### 7.1 REST API Endpoints

**Base URL:** `http://your-domain/api/v1/`

**Authentication:**
All API endpoints (except `/auth/login`) require authentication via Bearer token.

```http
Authorization: Bearer {your_token_here}
```

### 7.2 Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

Request Body:
{
  "email": "student@isufst.edu.ph",
  "password": "password123"
}

Response (200 OK):
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "student@isufst.edu.ph",
    "first_name": "Juan",
    "last_name": "Cruz",
    "role": "student"
  }
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {token}

Response (200 OK):
{
  "id": 1,
  "email": "student@isufst.edu.ph",
  "first_name": "Juan",
  "last_name": "Cruz",
  "role": "student",
  "created_at": "2026-01-15T08:00:00Z"
}
```

### 7.3 Appointment Endpoints

#### Get All Appointments (Student)
```http
GET /api/v1/appointments
Authorization: Bearer {token}

Response (200 OK):
[
  {
    "id": 1,
    "service_type": "Medical",
    "appointment_date": "2026-02-15",
    "start_time": "09:00:00",
    "end_time": "09:30:00",
    "status": "Confirmed",
    "reason": "Annual check-up",
    "created_at": "2026-02-01T10:30:00Z"
  }
]
```

#### Get Appointment Details
```http
GET /api/v1/appointments/1
Authorization: Bearer {token}

Response (200 OK):
{
  "id": 1,
  "service_type": "Medical",
  "appointment_date": "2026-02-15",
  "start_time": "09:00:00",
  "status": "Confirmed",
  "student": {
    "id": 5,
    "name": "Juan Cruz",
    "email": "juan@isufst.edu.ph"
  },
  "assigned_doctor": {
    "id": 3,
    "name": "Dr. Katherine Bicodo"
  }
}
```

#### Book Appointment
```http
POST /api/v1/appointments
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
  "service_type": "Dental",
  "appointment_date": "2026-02-20",
  "start_time": "14:00",
  "reason": "Tooth extraction"
}

Response (201 Created):
{
  "success": true,
  "appointment_id": 25,
  "message": "Appointment booked successfully"
}
```

#### Cancel Appointment
```http
POST /api/v1/appointments/25/cancel
Authorization: Bearer {token}

Response (200 OK):
{
  "success": true,
  "message": "Appointment cancelled"
}
```

#### Check Availability
```http
GET /api/v1/appointments/availability?date=2026-02-20&service_type=Medical
Authorization: Bearer {token}

Response (200 OK):
{
  "date": "2026-02-20",
  "service_type": "Medical",
  "available_slots": [
    {"time": "09:00", "available": 2},
    {"time": "09:30", "available": 1},
    {"time": "10:00", "available": 3}
  ]
}
```

### 7.4 Medical Records Endpoints

#### Get Medical History
```http
GET /api/v1/medical-records
Authorization: Bearer {token}

Response (200 OK):
[
  {
    "id": 12,
    "visit_date": "2026-01-10T10:00:00Z",
    "chief_complaint": "Headache",
    "diagnosis": "Tension headache",
    "treatment": "Rest and hydration",
    "status": "Completed"
  }
]
```

### 7.5 Medicine Endpoints

#### Get Available Medicines
```http
GET /api/v1/medicines
Authorization: Bearer {token}

Response (200 OK):
[
  {
    "id": 5,
    "medicine_name": "Paracetamol 500mg",
    "category": "Pain Reliever",
    "quantity": 150,
    "unit": "tablets",
    "available": true
  }
]
```

#### Get User's Reservations
```http
GET /api/v1/reservations
Authorization: Bearer {token}

Response (200 OK):
[
  {
    "id": 8,
    "medicine_name": "Amoxicillin 500mg",
    "quantity": 10,
    "status": "Ready",
    "reserved_at": "2026-02-01T14:00:00Z"
  }
]
```

#### Reserve Medicine
```http
POST /api/v1/reservations
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
  "medicine_id": 5,
  "quantity": 10
}

Response (201 Created):
{
  "success": true,
  "reservation_id": 15,
  "message": "Medicine reserved successfully"
}
```

### 7.6 Notification Endpoints

#### Get Notifications
```http
GET /api/v1/notifications
Authorization: Bearer {token}

Response (200 OK):
[
  {
    "id": 22,
    "title": "Appointment Reminder",
    "message": "Your appointment is tomorrow at 9:00 AM",
    "type": "appointment",
    "is_read": false,
    "created_at": "2026-02-14T08:00:00Z"
  }
]
```

#### Mark Notification as Read
```http
POST /api/v1/notifications/22/read
Authorization: Bearer {token}

Response (200 OK):
{
  "success": true
}
```

### 7.7 Feedback Endpoints

#### Submit Visit Feedback
```http
POST /api/v1/feedback
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
  "visit_id": 12,
  "rating": 5,
  "wait_time_rating": 4,
  "staff_rating": 5,
  "facility_rating": 5,
  "comments": "Excellent service!",
  "is_anonymous": false
}

Response (201 Created):
{
  "success": true,
  "message": "Feedback submitted"
}
```

### 7.8 Health Summary Endpoint

#### Get Comprehensive Health Data
```http
GET /api/v1/health-summary
Authorization: Bearer {token}

Response (200 OK):
{
  "statistics": {
    "total_visits": 12,
    "total_appointments": 15,
    "active_reservations": 2
  },
  "upcoming_appointments": [
    {
      "id": 25,
      "service_type": "Dental",
      "date": "2026-02-20",
      "time": "14:00"
    }
  ],
  "recent_visits": [
    {
      "id": 12,
      "date": "2026-01-10",
      "diagnosis": "Common cold"
    }
  ]
}
```

---

## 8. User Roles & Permissions

### 8.1 Role Definitions

The system implements Role-Based Access Control (RBAC) with 4 primary roles:

| Role | Description | Count |
|------|-------------|-------|
| **Student** | Registered ISUFST students | 500+ |
| **Nurse** | Clinic nursing staff | 3-5 |
| **Doctor** | Medical officers and dentists | 2-4 |
| **Admin** | System administrators | 1-2 |

### 8.2 Permission Matrix

| Feature | Student | Nurse | Doctor | Admin |
|---------|---------|-------|--------|-------|
| **Authentication** |
| Register Account | ✅ | ❌ | ❌ | ❌ |
| Login/Logout | ✅ | ✅ | ✅ | ✅ |
| View Own Profile | ✅ | ✅ | ✅ | ✅ |
| Edit Own Profile | ✅ | ✅ | ✅ | ✅ |
| **Appointments** |
| Book Appointment | ✅ | ❌ | ❌ | ❌ |
| View Own Appointments | ✅ | ❌ | ❌ | ❌ |
| Cancel Own Appointment | ✅ | ❌ | ❌ | ❌ |
| View All Appointments | ❌ | ✅ | ✅ | ✅ |
| Update Appointment Status | ❌ | ✅ | ✅ | ✅ |
| Assign/Change Doctor | ❌ | ❌ | ❌ | ✅ |
| **Medicine Reservations** |
| Browse Medicines | ✅ (Public) | ✅ | ✅ | ✅ |
| Reserve Medicine | ✅ | ❌ | ❌ | ❌ |
| View Own Reservations | ✅ | ❌ | ❌ | ❌ |
| View All Reservations | ❌ | ✅ | ✅ | ✅ |
| Mark Ready/Picked Up | ❌ | ✅ | ✅ | ✅ |
| **Inventory Management** |
| View Inventory | ❌ | ✅ | ✅ | ✅ |
| Add Medicine | ❌ | ✅ | ❌ | ✅ |
| Edit Medicine | ❌ | ✅ | ❌ | ✅ |
| Delete Medicine | ❌ | ❌ | ❌ | ✅ |
| **Queue Management** |
| View Queue (Public Display) | ✅ | ✅ | ✅ | ✅ |
| Manage Queue | ❌ | ✅ | ✅ | ✅ |
| Add to Queue | ❌ | ✅ | ✅ | ✅ |
| Call Next Patient | ❌ | ✅ | ✅ | ✅ |
| **Clinic Logbook** |
| View Logbook | ❌ | ✅ | ✅ | ✅ |
| Check-In Patient | ❌ | ✅ | ✅ | ✅ |
| Check-Out Patient | ❌ | ✅ | ✅ | ✅ |
| Scan QR Code | ❌ | ✅ | ✅ | ✅ |
| **Medical Records** |
| View Own Visits | ✅ | ❌ | ❌ | ❌ |
| View All Visits | ❌ | ✅ | ✅ | ✅ |
| Create Visit Record | ❌ | ✅ | ✅ | ✅ |
| Write Prescription | ❌ | ❌ | ✅ | ✅ |
| **Analytics & Reports** |
| View Analytics | ❌ | ✅ | ✅ | ✅ |
| Export Reports | ❌ | ❌ | ❌ | ✅ |
| **User Management** |
| View Users | ❌ | ❌ | ❌ | ✅ |
| Edit Users | ❌ | ❌ | ❌ | ✅ |
| Delete Users | ❌ | ❌ | ❌ | ✅ |
| **System** |
| View Audit Logs | ❌ | ❌ | ❌ | ✅ |
| Manage Doctor Schedules | ❌ | ❌ | ❌ | ✅ |
| System Configuration | ❌ | ❌ | ❌ | ✅ |

### 8.3 Permission Implementation

**Decorators in `rbac.py`:**

```python
@require_permission(Permission.VIEW_ANALYTICS)
def analytics_dashboard():
    # Only accessible to users with VIEW_ANALYTICS permission
    pass

@require_staff
def admin_dashboard():
    # Only accessible to staff (nurse, doctor, admin)
    pass

@student_only
def book_appointment():
    # Only students can book appointments
    pass
```

---

## 9. Installation & Deployment

### 9.1 System Requirements

**Software Requirements:**
- Python 3.11 or higher
- Node.js 18+ and npm (for Tailwind CSS)
- Git

**Database:**
- Turso account (free tier available at turso.tech)
- Or local SQLite for development

**External Services (Optional but Recommended):**
- Gmail account (for email notifications)
- Semaphore API account (for SMS notifications - Philippine provider)
- Google Cloud account (for Gemini AI API)

### 9.2 Local Development Setup

**Step 1: Clone Repository**
```bash
git clone <your-repo-url>
cd clinic
```

**Step 2: Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 3: Install Python Dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Install Node.js Dependencies**
```bash
npm install
```

**Step 5: Configure Environment Variables**

Create `.env` file in project root:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Database
DATABASE_URL=libsql://your-turso-db.turso.io
TURSO_AUTH_TOKEN=your_turso_auth_token

# Flask
SECRET_KEY=your-secret-key-here-use-secrets-token-urlsafe
FLASK_ENV=development

# Email (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=noreply@isufst.edu.ph

# SMS (Semaphore - Philippine provider)
SEMAPHORE_API_KEY=your-semaphore-api-key

# AI (Google Gemini)
GEMINI_API_KEY=your-gemini-api-key
```

**Step 6: Run Database Migration**
```bash
python migrate_database.py
```

**Step 7: Create Admin Account**
```bash
flask seed-admin
# Default credentials: admin@isufst.edu.ph / admin123
```

**Step 8: Build Production CSS (Optional)**

For development you can use CDN Tailwind (already configured), but for production:
```bash
npm run build:css
```

For live CSS updates during development:
```bash
npm run watch:css
```

**Step 9: Run the Application**
```bash
python app.py
```

The app will run at: `http://localhost:5000`

### 9.3 Production Deployment (Render.com)

**Prerequisite:** Create account at render.com

**Step 1: Prepare for Deployment**

Ensure `render.yaml` exists in project root:
```yaml
services:
  - type: web
    name: carehub
    env: python
    buildCommand: "pip install -r requirements.txt && npm install && npm run build:css"
    startCommand: "gunicorn app:app"
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: TURSO_AUTH_TOKEN
        sync: false
      - key: SECRET_KEY
        sync: false
```

**Step 2: Push to GitHub**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

**Step 3: Connect to Render**
1. Go to render.com dashboard
2. Click "New+" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Add environment variables in Render dashboard

**Step 4: Deploy**
- Render will automatically build and deploy
- Monitor build logs for errors
- Once deployed, your app will be live at `https://your-app.onrender.com`

### 9.4 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Turso database URL | `libsql://db.turso.io` |
| `TURSO_AUTH_TOKEN` | Yes | Turso auth token | `eyJhbGc...` |
| `SECRET_KEY` | Yes | Flask secret key | `secrets.token_urlsafe(32)` |
| `MAIL_SERVER` | No | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | No | SMTP port | `587` |
| `MAIL_USERNAME` | No | Email username | `yourname@gmail.com` |
| `MAIL_PASSWORD` | No | Email app password | Generated from Gmail |
| `SEMAPHORE_API_KEY` | No | SMS API key | `abc123...` |
| `GEMINI_API_KEY` | No | Google AI API key | `AIzaSy...` |

**Security Note:** Never commit `.env` file to version control. Always use `.env.example` as template.

### 9.5 Database Migration Commands

**Create Migration:**
```bash
flask db migrate -m "Description of changes"
```

**Apply Migration:**
```bash
flask db upgrade
```

**Rollback Migration:**
```bash
flask db downgrade
```

**View Migration History:**
```bash
flask db history
```

---

## 10. User Workflows

### 10.1 Student Workflows

#### A. Book an Appointment

```
1. Student logs in → /auth/login
2. Click "Book Appointment" → /appointments/book
3. Select service type (Medical/Dental)
4. Choose date from calendar (shows real-time availability)
5. Select time slot (color-coded: green = available, red = full)
6. Enter reason for visit
7. Click "Book Appointment"
8. System checks availability
9. Auto-assigns available doctor
10. Generates QR code for check-in
11. Sends confirmation email
12. Sends SMS reminder 24 hours before
13. Student receives notification → /dashboard
```

#### B. Reserve Medicine

```
1. Student visits /reservations/medicines (can be done without login)
2. Browse available medicines
3. Search by name or filter by category
4. Click "Reserve" on desired medicine
5. If not logged in → prompted to login
6. Select quantity (system validates against stock)
7. Click "Confirm Reservation"
8. System generates QR code for pickup
9. Locks inventory stock atomically
10. Sends email: "Your medicine is reserved"
11. Nurse marks as "Ready" when prepared
12. Student receives SMS: "Medicine ready for pickup"
13. Student shows QR at clinic
14. Staff scans QR → marks as "Picked Up"
15. Inventory auto-deducted
```

#### C. View Health Timeline

```
1. Student logs in
2. Navigate to /dashboard
3. View unified health timeline showing:
   - Upcoming appointments
   - Past clinic visits
   - Active medicine reservations
   - Health certificates
4. Click on any item for details
5. Filter by date range
6. Export visit history (future feature)
```

#### D. Use Symptom Checker

```
1. Student visits /screening/
2. Select symptoms from multiple categories
3. Enter additional information (duration, severity)
4. Click "Get Recommendation"
5. AI analyzes symptoms via Gemini API
6. System recommends service type (Medical/Dental/Emergency)
7. Provides urgency level (Low/Medium/High)
8. If urgent → shows emergency disclaimer
9. If non-urgent → pre-fills appointment booking form
10. Student clicks "Book Appointment" → redirected with pre-filled data
```

### 10.2 Nurse/Staff Workflows

#### A. Manage Daily Queue

```
1. Staff logs in
2. Navigate to /queue/
3. View today's queue:
   - Waiting patients
   - Currently serving
   - Completed entries
4. Call next patient → Click "Call Next"
5. Patient's name appears on TV display (/queue-display/)
6. Mark as "In Progress"
7. After consultation → Click "Complete"
8. Next patient auto-queued
```

#### B. Check-In Patient with QR Code

```
1. Staff opens /logbook/
2. Click "Scan QR Code"
3. Two options appear:
   a. Camera Tab: Hold QR to camera → auto-scans
   b. Manual Tab: Type/paste QR data
4. System verifies QR token
5. If valid:
   - Appointment QR → Pre-fills student info, service type, appointment details
   - Medicine QR → Pre-fills for medicine pickup
6. Staff confirms check-in
7. Entry logged in digital logbook
8. Patient added to queue if not already present
```

#### C. Process Medicine Reservation Pickup

```
1. Student arrives with QR code (email/phone screenshot)
2. Staff opens /logbook/ → Click "Scan QR"
3. Scan student's reservation QR
4. System verifies reservation
5. Displays:
   - Student name
   - Medicine name & quantity
   - Reservation date
6. Staff confirms pickup
7. System marks reservation as "Picked Up"
8. Inventory auto-deducted
9. Entry logged in logbook
```

### 10.3 Admin Workflows

#### A. View Analytics Dashboard

```
1. Admin logs in
2. Navigate to /analytics/
3. View real-time metrics:
   - Today's appointments/visits
   - Monthly statistics
   - Service type distribution (pie chart)
   - Peak hours heatmap
   - Doctor workload balance
   - Satisfaction ratings trend
   - No-show rate
   - Inventory consumption
4. Filter by date range
5. Export data as CSV (future feature)
6. Print reports
```

#### B. Manage Inventory

```
1. Admin navigates to /inventory/
2. View all medicines with:
   - Stock levels
   - Expiry dates (highlighted if < 30 days)
   - Low stock alerts (<10 units)
3. Add new medicine:
   - Name, category, quantity
   - Expiry date, batch number
4. Edit existing medicine
5. Delete medicine (only if no active reservations)
6. Receive weekly email:
   - Expiring medicines list
   - Low stock items
```

#### C. User Management

```
1. Admin navigates to /auth/users
2. View all registered users (students, staff)
3. Search by name/email
4. Click user → Edit details:
   - Change role (student/nurse/doctor/admin)
   - Activate/deactivate account
   - Reset password (feature: send reset link)
5. View user activity:
   - Last login
   - Total appointments
   - Total visits
6. Audit log tracking (who changed what, when)
```

---

## 11. Security & Compliance

### 11.1 Authentication & Authorization

**Password Security:**
- Passwords hashed using Werkzeug's `generate_password_hash()` (PBKDF2-SHA256)
- No plain-text password storage
- Minimum password length enforced (8 characters)

**Session Management:**
- Flask-Login handles user sessions
- Secure session cookies (httponly, samesite)
- Session timeout after inactivity
- "Remember me" option available

**Role-Based Access Control (RBAC):**
- Implemented in `rbac.py`
- Decorators enforce permissions on every route

### 11.2 CSRF Protection

**Implementation:**
- Flask-WTF provides CSRF protection
- Every form includes CSRF token:
  ```html
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ```
- AJAX requests include token in headers:
  ```javascript
  headers: {
    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
  }
  ```

### 11.3 Data Privacy

**Health Data Protection:**
- Medical records only accessible to:
  - Patient (own records)
  - Treating doctor/nurse
  - Admin (with audit trail)
- No export of patient data without authorization
- Anonymized feedback option

**Philippine DPA Compliance:**
- Data minimization (collect only necessary info)
- Purpose limitation (use data only for healthcare)
- Data retention policies

### 11.4 Audit Logging

**What is Logged:**
- All login/logout events
- User CRUD operations (create, update, delete)
- Medical record access
- Inventory changes
- Appointment modifications

**Audit Log Fields:**
```json
{
  "user_id": 5,
  "action": "UPDATE",
  "entity_type": "Appointment",
  "entity_id": 12,
  "old_value": {"status": "Pending"},
  "new_value": {"status": "Completed"},
  "ip_address": "192.168.1.100",
  "timestamp": "2026-02-15T14:30:00Z"
}
```

### 11.5 QR Code Security

**Token Generation:**
- Secure random tokens using Python's `secrets.token_urlsafe(32)`
- 256-bit entropy
- Tokens stored hashed in database

**Expiration:**
- Appointment QR: Valid until 30 days after appointment
- Reservation QR: Valid until picked up or 7 days (auto-cancel)

### 11.6 SQL Injection Prevention

**ORM Protection:**
- SQLAlchemy ORM used for all DB queries
- Parameterized queries (no raw SQL)
- Example:
  ```python
  # SECURE (SQLAlchemy ORM)
  user = User.query.filter_by(email=email).first()
  ```

### 11.7 Input Validation

**Server-Side Validation:**
- All form inputs validated via Flask-WTF validators
- Data sanitization before DB insertion
- Email format verification
- Date/time format checks

**Client-Side Validation:**
- HTML5 form validation (required, email, date)
- JavaScript validation for better UX (not relied upon for security)

### 11.8 Secure Communication

**HTTPS in Production:**
- Render.com automatically provides SSL certificates
- All traffic encrypted with TLS 1.3

**API Security:**
- Token-based authentication (Bearer tokens)
- Tokens expire after 30 days
- CORS configured for specific origins only

---

## 12. Testing & Quality Assurance

### 12.1 Testing Strategy

**Test Pyramid:**
```
        /\
       /  \     E2E Tests (Few)
      /____\
     /      \   Integration Tests (Some)
    /________\
   /          \ Unit Tests (Many)
  /__________\
```

### 12.2 Manual Testing Checklist

**Authentication:**
- [ ] Register new student account
- [ ] Login with correct credentials
- [ ] Login with wrong credentials (should fail)
- [ ] Logout functionality
- [ ] Session persistence (refresh page while logged in)
- [ ] Access protected routes without login (should redirect)

**Appointments:**
- [ ] Book appointment with available slot
- [ ] Try booking past date (should fail)
- [ ] Try booking fully booked slot (should fail)
- [ ] View own appointments
- [ ] Cancel appointment
- [ ] QR code generation on booking
- [ ] QR code verification at clinic
- [ ] Email confirmation received
- [ ] SMS reminder 24 hours before

**Medicine Reservations:**
- [ ] Browse public medicine catalog (not logged in)
- [ ] Reserve medicine while logged in
- [ ] Try reserving more than available stock (should fail)
- [ ] QR code generation on reservation
- [ ] Staff marks reservation as "Ready"
- [ ] Student receives email notification
- [ ] QR code scan for pickup
- [ ] Inventory auto-deducted after pickup

**Queue Management:**
- [ ] Add patient to queue manually
- [ ] Auto-enqueue from appointment
- [ ] Call next patient
- [ ] TV display updates in real-time (WebSocket)
- [ ] Complete queue entry
- [ ] Remove from queue

**Analytics:**
- [ ] View dashboard (staff only)
- [ ] Charts render correctly (Chart.js)
- [ ] Filter by date range
- [ ] Data accuracy (spot-check numbers)

**Notifications:**
- [ ] Email notifications send correctly
- [ ] SMS notifications send (if API key configured)
- [ ] In-app notifications appear
- [ ] Mark notification as read
- [ ] Notification count updates

**Symptom Checker:**
- [ ] Select symptoms
- [ ] AI analysis returns recommendation
- [ ] Urgency level displayed
- [ ] Pre-fill appointment booking

**QR Scanner:**
- [ ] Camera scanner detects QR code
- [ ] Manual input fallback works
- [ ] Invalid QR shows error
- [ ] Valid QR pre-fills form

### 12.3 Browser Compatibility

**Tested Browsers:**
- Chrome 100+ ✅
- Firefox 90+ ✅
- Safari 15+ ✅
- Edge 100+ ✅
- Mobile Safari (iOS) ✅
- Chrome Mobile (Android) ✅

**Responsive Design:**
- Desktop (1920x1080) ✅
- Laptop (1366x768) ✅
- Tablet (768x1024) ✅
- Mobile (375x667) ✅

---

## 13. Future Enhancements

### 13.1 Phase 2 Features

**1. Telemedicine Video Consultations**
- **Technology:** WebRTC (via Twilio or Agora SDK)
- **Features:**
  - Video/audio calls between student and doctor
  - Screen sharing for showing symptoms
  - Chat during consultation
  - Call recording (with consent)

**2. Mobile Applications**
- **Platform:** Flutter (cross-platform iOS/Android)
- **Features:**
  - Native mobile UI
  - Push notifications (Firebase Cloud Messaging)
  - Offline mode (local SQLite cache)
  - Biometric login (fingerprint/face ID)
  - Consume existing REST API (`/api/v1/`)

**3. Laboratory Test Management**
- **Features:**
  - Request lab tests (CBC, urinalysis, etc.)
  - Track test status (Pending → In Progress → Completed)
  - Upload/view test results (PDF)
  - Link results to clinic visits

**4. Advanced Analytics**
- **Machine Learning:**
  - Predictive no-show rate
  - Peak time forecasting
  - Disease outbreak detection (multiple same diagnoses)
- **Data Visualization:**
  - Interactive dashboards (Plotly Dash)
  - Export to Excel/PDF reports

**5. Multi-Language Support**
- **Languages:** English, Filipino (Tagalog), Hiligaynon (local dialect)
- **Technology:** Flask-Babel for i18n
- **UI:** Language switcher in navbar

**6. Dark Mode**
- **Implementation:** CSS custom properties + Tailwind dark mode
- **Storage:** User preference saved in database

**7. Progressive Web App (PWA)**
- **Features:**
  - Installable on mobile home screen
  - Offline functionality (Service Workers)
  - Push notifications (Web Push API)

### 13.2 Technical Improvements

**1. Database Migration to PostgreSQL**
- **Why:** Better concurrent write performance for high traffic
- **When:** If user base exceeds 5,000 students

**2. Redis Caching**
- **Use Cases:**
  - Cache frequently accessed inventory data
  - Session storage (faster than DB)
  - Rate limiting for API

**3. Celery Background Tasks**
- **Replace:** APScheduler (current)
- **Use Cases:**
  - Asynchronous email sending
  - Scheduled report generation
  - Data backup jobs

**4. Microservices Architecture**
- **If system grows:**
  - Notification Service (separate app)
  - Analytics Service (separate app)
  - API Gateway (single entry point)

### 13.3 AI/ML Features

**1. Chatbot Improvements**
- Fine-tune on medical Q&A dataset
- Context-aware conversations (remember previous questions)
- Voice input (speech-to-text)

**2. Symptom-to-Diagnosis ML Model**
- Train on clinic visit data
- Input: Symptoms, vitals → Output: Predicted diagnosis

**3. Prescription Recommendation**
- Suggest medicines from inventory based on diagnosis
- Drug interaction warnings

---

## 14. Troubleshooting

### 14.1 Common Issues

#### Issue: Database Connection Error
```
Error: Unable to connect to Turso database
```

**Solution:**
1. Check `DATABASE_URL` in `.env` is correct
2. Verify `TURSO_AUTH_TOKEN` is valid
3. Test connection:
   ```bash
   python -c "from app import db; print(db.engine.url)"
   ```
4. Regenerate auth token if expired (turso.tech dashboard)

---

#### Issue: Email Notifications Not Sending
```
Error: SMTP authentication failed
```

**Solution:**
1. **Gmail users:** Enable "App Passwords" (not regular password)
   - Google Account → Security → 2-Step Verification → App Passwords
2. Check `.env` values
3. Test email manually:
   ```python
   from notification_service import send_email
   send_email('test@example.com', 'Test', 'Hello')
   ```

---

#### Issue: QR Code Scanner Not Working
```
Error: Camera access denied
```

**Solution:**
1. **Browser permission:** Allow camera access when prompted
2. **HTTPS required:** QR scanner only works on HTTPS (or localhost)
3. **Fallback:** Use "Manual Input" tab to paste QR data
4. Check browser console for JavaScript errors

---

#### Issue: Tailwind CSS Not Loading
```
Page appears unstyled (no colors, broken layout)
```

**Solution:**
1. **Development:** Use CDN (already configured in templates)
   ```html
   <script src="https://cdn.tailwindcss.com"></script>
   ```
2. **Production:** Build CSS:
   ```bash
   npm install
   npm run build:css
   ```
3. Check `static/css/output.css` exists

---

#### Issue: WebSocket Queue Display Not Updating
```
Queue display shows "Connecting..." forever
```

**Solution:**
1. Check Flask-SocketIO is installed:
   ```bash
   pip install flask-socketio
   ```
2. Verify WebSocket connection in browser console (F12)
3. **Firewall:** Ensure port 5000 is open
4. **Production:** Use `eventlet` or `gevent` WSGI server

---

#### Issue: Appointment Slots Showing as Unavailable

**Solution:**
1. Check timezone is set to Philippine time (Asia/Manila)
2. Clear old test data
3. Verify `MAX_APPOINTMENTS_PER_SLOT` configuration

---

### 14.2 Debugging Tips

**Enable Debug Mode:**
```python
# config.py
DEBUG = True  # Only for development!
```

**Check Flask Logs:**
```bash
FLASK_ENV=development python app.py
```

**Database Debugging:**
```python
flask shell
>>> from models import db, User
>>> db.session.query(User).all()
```

**Browser DevTools:**
1. Open Developer Console (F12)
2. **Network tab:** Check API requests/responses
3. **Console tab:** Check JavaScript errors
4. **Application tab:** View cookies, localStorage, session data

---

## 15. References & Credits

### 15.1 Technology Documentation

**Backend:**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)

**Frontend:**
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [Font Awesome Icons](https://fontawesome.com/)

**External Services:**
- [Turso Database](https://turso.tech/docs)
- [Google Gemini AI](https://ai.google.dev/)
- [Semaphore SMS API](https://semaphore.co/docs)

### 15.2 Development Team

**Project Leader:** [Your Name]  
**Developers:** [Team Members]  
**Advisers:** [Faculty Advisers]  
**Institution:** Iloilo State University of Fisheries Science and Technology  
**Year:** 2026

### 15.3 Open Source Libraries

| Library | License | Purpose |
|---------|---------|---------|
| Flask | BSD-3-Clause | Web framework |
| SQLAlchemy | MIT | Database ORM |
| Tailwind CSS | MIT | CSS framework |
| Chart.js | MIT | Data visualization |
| QRCode | BSD | QR code generation |
| ReportLab | BSD | PDF generation |
| HTML5-QRCode | Apache-2.0 | QR scanner |
| SweetAlert2 | MIT | Alert dialogs |

### 15.4 Contact

For questions, support, or contributions:
- **Email:** clinic-support@isufst.edu.ph
- **GitHub:** [Repository URL]

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Blueprint** | Flask's way of organizing routes into modules |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |
| **QR Code** | Quick Response code for check-in/pickup |
| **RBAC** | Role-Based Access Control |
| **CSRF** | Cross-Site Request Forgery (security protection) |
| **WebSocket** | Real-time bidirectional communication (Socket.IO) |
| **REST API** | Representational State Transfer API (JSON) |
| **JWT** | JSON Web Token (API authentication) |
| **SMTP** | Simple Mail Transfer Protocol (email) |
| **SMS** | Short Message Service (text messages) |
| **AI** | Artificial Intelligence (Gemini chatbot) |
| **PWA** | Progressive Web App |

---

## Appendix B: Database ER Diagram

```
┌─────────┐       ┌──────────────┐       ┌───────────┐
│  users  │───(1)─┤appointments  │──(1)──│appointment│
│         │       │              │       │_extended  │
└─────────┘       └──────────────┘       └───────────┘
     │                    │
     │                    │
    (∞)                  (1)
     │                    │
     │            ┌──────────────┐
     └────────────┤clinic_visits │
                  └──────────────┘
                         │
                        (∞)
                         │
                  ┌──────────────┐
                  │prescriptions │
                  └──────────────┘
                         │
                        (∞)
                         │
                  ┌─────────────────┐
                  │prescription_items│
                  └─────────────────┘
                         │
                        (∞)
                         │
                  ┌─────────┐
                  │inventory│
                  └─────────┘
```

---

## Appendix C: Deployment Checklist

Before deploying to production:

- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Generate strong `SECRET_KEY` (not default)
- [ ] Configure production database (Turso)
- [ ] Set up email SMTP (Gmail or SendGrid)
- [ ] Configure SMS API (Semaphore)
- [ ] Build production CSS (`npm run build:css`)
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up firewall rules
- [ ] Configure CORS for API
- [ ] Test all user workflows
- [ ] Set up backup schedule
- [ ] Create admin accounts
- [ ] Add seed data (medicines, services)
- [ ] Configure domain name
- [ ] Set up monitoring (Sentry or New Relic)
- [ ] Write deployment documentation
- [ ] Train clinic staff on system usage

---

## Appendix D: Capstone Defense Tips

**Demo Flow:**
1. **Student Journey:**
   - Show symptom checker → AI recommendation
   - Book appointment → Show QR code generation
   - View health timeline

2. **Staff Operations:**
   - Scan QR code for check-in
   - Manage queue → Show real-time TV display
   - Process medicine reservation pickup

3. **Admin Insights:**
   - Analytics dashboard → Show interactive charts
   - Inventory management → Low stock alerts
   - Audit logs → Compliance

**Talking Points:**
- **Integration:** "All modules are connected — appointments link to queue, visits, and prescriptions."
- **Innovation:** "AI symptom screening and real-time WebSocket queue display."
- **Scalability:** "REST API ready for mobile apps, production Tailwind build, modular architecture."
- **Security:** "RBAC, CSRF protection, audit logging, QR code security."
- **Business Logic:** "Not just CRUD — we have complete healthcare workflows."

**Questions to Prepare For:**
- Why Flask over Django? → Lightweight, flexible, no bloat
- Why Turso database? → Free, distributed SQLite, good for MVP
- How secure is patient data? → Encryption, RBAC, audit logs
- Can it scale to 10,000 students? → Yes, with PostgreSQL/Redis migration
- What makes it different from existing systems? → All-in-one, free, mobile-ready

---

**END OF DOCUMENTATION**

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Total Pages:** ~15,000 words  

**For future maintainers:**
This documentation covers the complete system as of February 2026. Update this file when adding new features or making architectural changes. Keep the "Future Enhancements" section updated with what's next.

**Good luck with your capstone defense! 🎓🏥**
