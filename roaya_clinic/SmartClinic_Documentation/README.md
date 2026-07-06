smart clinic Managment using odoo 17 
# Smart Clinic Management

A comprehensive clinic management module built on Odoo 17 that streamlines daily healthcare operations. The system provides an integrated solution for managing patients, doctors, appointments, laboratory requests, billing, CRM integration, website services, and patient portal access.

Developed as part of the NTI HireReady Program – Team A.

---

# Table of Contents

1. Introduction
2. Project Overview
3. Objectives
4. System Features
5. System Workflow
6. Core Modules
7. Project Architecture
8. Installation
9. Configuration
10. Website & Patient Portal
11. CRM Integration
12. Reports
13. Technical Highlights
14. Technologies Used
15. Future Enhancements
16. Team

---

# Introduction

Smart Clinic Management is an ERP module developed on top of Odoo 17 to automate and simplify the daily operations of a multi-specialty healthcare clinic.

The system provides a centralized environment where receptionists, doctors, and clinic managers can manage appointments, patient records, laboratory requests, and billing information while maintaining an organized workflow throughout the patient's visit.

The module also integrates with several Odoo applications including CRM, Website, Portal, Mail, and Web to provide a complete healthcare management solution.

---

# Project Overview

The project was designed to replace traditional paper-based clinic management with a centralized ERP solution.

The module manages the complete lifecycle of a patient's visit starting from registration and appointment booking, through medical examination and laboratory requests, until billing and reporting.

The system also includes a public website for presenting clinic information, a patient portal for accessing appointments, scheduled automation using cron jobs, email notifications, PDF reports, and REST API endpoints for future integrations.

---

# Objectives

The Smart Clinic module aims to achieve the following objectives:

- Centralize patient and doctor information.
- Simplify appointment scheduling.
- Prevent appointment conflicts.
- Manage laboratory requests.
- Track clinic charges and payments.
- Improve communication using automated email reminders.
- Provide online services through the clinic website.
- Allow patients to access their appointments through a portal.
- Integrate clinic requests with the Odoo CRM application.
- Generate printable reports for patients and appointments.

---

# System Features

Patient Management

- Register new patients.
- Store personal and medical information.
- Record blood type and allergies.
- Automatically calculate patient age.
- Link patients with portal users.
- Generate patient medical reports.

Doctor Management

- Manage doctor profiles.
- Assign medical specialties.
- Store consultation fees.
- Manage weekly schedules.
- Publish doctors on the website.
- Track daily appointment statistics.

Appointment Management

- Create appointments.
- Assign doctors.
- Automatically retrieve specialties.
- Calculate appointment duration.
- Prevent scheduling conflicts.
- Track appointment status.
- Send reminder emails automatically.
- Detect No-Show appointments.
- Generate appointment confirmation reports.

Laboratory Management

- Create laboratory orders.
- Support multiple laboratory test types.
- Define urgency levels.
- Record laboratory results.
- Track laboratory costs.

Billing Management

- Create consultation charges.
- Create laboratory charges.
- Calculate total payable amounts.
- Support multiple payment methods.
- Track payment status.

Website

- Home page.
- About page.
- Services page.
- Doctors page.
- Contact page.

Patient Portal

- View appointments.
- Access laboratory results.
- Manage patient profile.
- View dashboard information.

CRM Integration

- Manage incoming patient requests.
- Record request sources.
- Assign doctors.
- Prepare requests for conversion into clinic records.

Reporting

- Appointment Report.
- Patient Medical Report.

Automation

- Appointment reminder emails.
- Automatic No-Show detection.
- Automatic sequence generation.

REST API

- API authentication using tokens.
- Appointment endpoints.
- Doctor endpoints.
- Integration-ready architecture.

---

# System Workflow

```text
Patient Registration
        │
        ▼
Doctor Selection
        │
        ▼
Appointment Booking
        │
        ▼
Appointment Confirmation
        │
        ▼
Patient Check-In
        │
        ▼
Medical Examination
        │
        ├───────────────┐
        ▼               ▼
 Laboratory Order    Billing
        │               │
        └───────┬───────┘
                ▼
      Appointment Completed
                │
                ▼
      Reports & Patient Portal
```

---

# Core Modules

| Module | Responsibility |
|---------|----------------|
| Patient | Stores patient personal and medical information |
| Doctor | Manages doctor profiles and specialties |
| Specialty | Organizes medical specialties |
| Appointment | Handles appointment scheduling and workflow |
| Lab Order | Manages laboratory requests and results |
| Charge | Handles clinic billing and payments |
| API Token | Provides authentication for REST APIs |
| CRM Lead | Extends CRM for patient request management |

---

# Project Architecture

The Smart Clinic module follows the standard Odoo modular architecture to ensure maintainability, scalability, and separation of concerns.

```text
smart_clinic/
│
├── controllers/
│   ├── api.py
│   ├── controllers.py
│   ├── website.py
│   └── portal.py
│
├── models/
│   ├── patient.py
│   ├── doctor.py
│   ├── specialty.py
│   ├── appointment.py
│   ├── lab_order.py
│   ├── charge.py
│   ├── api_token.py
│   └── crm_lead.py
│
├── views/
│   ├── patient_views.xml
│   ├── doctor_views.xml
│   ├── specialty_views.xml
│   ├── appointment_views.xml
│   ├── lab_order_views.xml
│   ├── charge_views.xml
│   ├── api_token_views.xml
│   ├── crm_lead_views.xml
│   ├── website/
│   └── portal/
│
├── report/
│
├── wizard/
│
├── security/
│
├── static/
│
├── data/
│
└── demo/
```

The project follows the MVC (Model–View–Controller) design pattern used by Odoo.

- Models contain business logic and database objects.
- Views define the user interface.
- Controllers manage website pages, portal routes, and REST APIs.
- Wizards provide interactive operations.
- Reports generate printable PDF documents.
- Data contains sequences, scheduled actions, and email templates.

---

# Installation

Clone the repository

```bash
git clone https://github.com/your-repository/smart_clinic.git
```

Move the module into the custom addons directory.

Restart the Odoo server.

Update the Apps List.

Search for:

```
Smart Clinic Management
```

Click **Install**.

---

# Dependencies

The module depends on the following Odoo applications:

- Base
- Web
- Mail
- Website
- Portal
- CRM

Python dependencies:

- xlsxwriter

---

# Configuration

After installation:

- Create clinic specialties.
- Create doctors.
- Create patients.
- Configure appointment sequences.
- Configure scheduled actions.
- Configure outgoing email server.
- Configure portal users if required.

The module is now ready for daily clinic operations.

---

# Patient Management

The Patient module stores all patient information in a centralized database.

Features include:

- Patient registration
- Contact information
- Medical profile
- Blood type
- Allergies
- Portal account linkage
- Profile image
- Automatic age calculation

Business Rules

- Email addresses must be unique.
- Age is calculated automatically.
- Patients can be archived without deleting records.

---

# Doctor Management

The Doctor module manages clinic physicians and their schedules.

Features include:

- Doctor profiles
- Specialties
- Medical licenses
- Consultation fees
- Weekly schedules
- Website publishing
- Daily appointment statistics

Business Rules

- Each doctor belongs to one specialty.
- License numbers must be unique.
- Doctor email and phone are synchronized with the linked Odoo user.

---

# Appointment Management

The Appointment module represents the core business process of the system.

It manages the entire patient visit lifecycle.

Appointment States

```
Draft

↓

Confirmed

↓

Checked In

↓

In Progress

↓

Done
```

Alternative States

```
Cancelled

No Show
```

Main Features

- Appointment booking
- Doctor assignment
- Automatic specialty assignment
- Duration calculation
- Conflict detection
- Status tracking
- Reminder emails
- No-Show automation
- Appointment reports

Business Rules

- Start time must be earlier than end time.
- Doctors cannot have overlapping appointments.
- Appointment duration is calculated automatically.
- Reminder emails are sent automatically before appointments.
- Missed appointments are automatically marked as No Show.

---

# Laboratory Management

Laboratory requests are linked directly to appointments.

Supported Tests

- Blood Test
- Urine Test
- X-Ray
- CT Scan
- MRI

Urgency Levels

- Low
- Medium
- High
- Emergency

Workflow

```
Draft

↓

Ordered

↓

In Progress

↓

Done
```

Each laboratory order stores:

- Patient
- Doctor
- Appointment
- Test type
- Description
- Result
- Cost
- Completion date

---

# Billing Management

The Charge module manages clinic financial transactions.

Charge Types

- Consultation
- Laboratory
- Prescription
- Other

Payment Methods

- Cash
- Card
- Insurance

Workflow

```
Draft

↓

Pending

↓

Paid
```

Automatic Calculation

```
Total Amount = Amount + Late Fee
```

Each charge stores:

- Appointment
- Patient
- Doctor
- Amount
- Late Fee
- Total Amount
- Due Date
- Payment Date
- Payment Method

---

# Website

The module includes a public website built using Odoo Website.

Available pages include:

- Home
- About
- Services
- Doctors
- Contact

Patients can browse clinic information before contacting the clinic.

---

# Patient Portal

Authenticated patients can access a personal portal.

Portal Features

- View appointments
- View laboratory results
- Dashboard
- Profile management

The portal provides secure access to patient information.

---

# CRM Integration

The module extends the standard CRM application.

Receptionists can manage patient requests before creating clinic records.

Lead Sources

- Website
- API
- Manual

Stored Information

- Doctor
- Requested specialty
- Requested appointment
- Internal notes

---

# Reports

The module includes printable PDF reports.

Available Reports

- Appointment Report
- Patient Medical Report

Reports can be printed directly from Odoo.

---

# Email Automation

Scheduled actions automatically send reminder emails before confirmed appointments.

Benefits include:

- Reduced missed appointments
- Better patient communication
- Automated workflow

---

# REST API

The module exposes REST endpoints for future integrations.

Supported services include:

- Authentication
- Appointment operations
- Doctor information

The API is secured using API Tokens.

---

# Security

The system uses Odoo security mechanisms.

Security features include:

- Access Control Lists
- User Groups
- Portal Users
- Record Rules
- Authentication
- API Tokens

---

# Technical Highlights

The project demonstrates the use of several Odoo development concepts.

Models

- Computed Fields
- Related Fields
- Selection Fields
- SQL Constraints
- Many2one Relations
- Method Override
- Sequences

Business Logic

- Onchange Methods
- Constraints
- Scheduled Actions
- Email Templates
- Automatic Calculations

Framework Features

- Mail Thread
- Activity Management
- Portal
- Website
- Controllers
- REST API
- PDF Reports
- Wizards

---

# Technologies Used

Backend

- Python
- Odoo 17 ORM

Frontend

- XML
- QWeb
- HTML
- CSS
- JavaScript

Database

- PostgreSQL

Framework

- Odoo 17

Version Control

- Git
- GitHub

---

# Future Enhancements

Future versions of the system may include:

- Online payment integration
- SMS notifications
- Medical prescriptions
- Appointment calendar synchronization
- Multi-branch support
- Doctor availability calendar
- Analytics dashboard
- Mobile application integration

---

# Team

Developed as part of the NTI HireReady Program.

Team A

Module

Smart Clinic Management

Framework

Odoo 17 ERP

License

LGPL-3
---

# Business Rules

The Smart Clinic module enforces several business rules to ensure data consistency and prevent invalid operations.

### Patient Rules

- Each patient must have a unique email address.
- Patient age is calculated automatically from the date of birth.
- Patients can be archived without deleting their records.

### Doctor Rules

- Every doctor must belong to a specialty.
- Doctor license numbers must be unique.
- Doctor contact information is linked to the associated Odoo user.

### Appointment Rules

- Appointment start time must be earlier than the end time.
- Doctors cannot have overlapping appointments.
- The appointment specialty is automatically assigned based on the selected doctor.
- Appointment duration is calculated automatically.
- Reminder emails are sent automatically before confirmed appointments.
- Missed appointments are automatically marked as **No Show**.

### Laboratory Rules

- Every laboratory order must belong to an appointment.
- Patient and doctor information are automatically inherited from the related appointment.
- Each laboratory order receives an automatically generated sequence number.

### Billing Rules

- Every charge must belong to an appointment.
- Patient and doctor information are automatically inherited from the related appointment.
- Total Amount is calculated automatically.

---

# Folder Description

| Folder | Description |
|---------|-------------|
| controllers | Website pages, Portal routes, and REST API controllers |
| models | Business logic and database models |
| views | Form, Tree, Search, Kanban, Website, and Portal views |
| report | PDF report templates |
| wizard | Interactive wizard forms |
| security | Access control lists and security configuration |
| data | Sequences, cron jobs, and email templates |
| demo | Demonstration records |
| static | CSS and JavaScript assets |

---

# Odoo Features Used

The Smart Clinic module demonstrates the use of several Odoo framework features.

### ORM

- Models
- Fields
- Related Fields
- Computed Fields
- Stored Computed Fields
- Selection Fields
- Many2one Relationships
- SQL Constraints
- Method Override

### Business Logic

- @api.depends
- @api.onchange
- @api.constrains
- Scheduled Actions (Cron Jobs)
- Automatic Sequence Generation
- Validation Rules

### User Interface

- Form Views
- Tree Views
- Search Views
- Menu Items
- Window Actions
- Website Templates
- Portal Templates

### Reporting

- QWeb PDF Reports
- Report Actions

### Communication

- Mail Thread
- Mail Activity
- Email Templates

### Integration

- CRM Integration
- Website Integration
- Patient Portal
- REST API
- API Token Authentication

---

# Database Relationships

The following diagram illustrates the main relationships between the system models.

```text
                  Specialty
                      │
                      │
                  Doctor
                      │
                      │
          ┌───────────┴───────────┐
          │                       │
       Appointment            CRM Lead
          │
          │
     ┌────┴─────┐
     │          │
 Patient    Lab Order
     │
     │
   Charge
```

---

# Module Dependencies

The Smart Clinic module depends on the following Odoo modules.

```text
base
 │
 ├── web
 ├── mail
 ├── website
 ├── portal
 └── crm
        │
        ▼
 Smart Clinic Management
```

---

# Technical Highlights

This project demonstrates practical implementation of core Odoo development concepts.

- Custom Odoo Models
- ORM Relationships
- Computed Fields
- Related Fields
- SQL Constraints
- Record Ordering
- Indexed Fields
- Business Validations
- Scheduled Actions
- Automatic Email Notifications
- Website Development
- Portal Development
- REST API Development
- QWeb Reports
- Sequence Management
- CRM Extension
- MVC Architecture

---

# Screenshots

The following screenshots can be added after deploying the project.

- Home Page
- Doctor List
- Patient List
- Appointment Form
- Laboratory Order
- Charge Form
- CRM Lead
- Patient Portal Dashboard
- Appointment Report
- Patient Medical Report

---

# Authors

Developed as part of the **NTI HireReady Program**.

**Project:** Smart Clinic Management

**Framework:** Odoo 17

**Programming Language:** Python

**Database:** PostgreSQL

**License:** LGPL-3

**Team:** Team A

---

# License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3)**.

---

# Acknowledgments

This project was developed as part of the NTI HireReady training program to demonstrate practical ERP development using Odoo 17.

Special thanks to the instructors, mentors, and team members who contributed to the successful completion of this project.










