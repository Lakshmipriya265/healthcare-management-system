# 🏥 Healthcare Management System

A web-based Healthcare Management System developed using Flask and SQLite to manage patients, doctors, nurses, appointments, prescriptions, and patient records.

## 📌 Project Overview

The Healthcare Management System provides a centralized platform for managing healthcare-related activities.

The system supports multiple user roles, allowing administrators, doctors, nurses, pharmacists, and patients to access features according to their responsibilities.

## ✨ Features

### 👨‍💼 Admin
- Admin dashboard
- Add and manage doctors
- Add and manage nurses
- Add and manage patients
- View appointments

### 👨‍⚕️ Doctor
- Doctor dashboard
- View patients
- View patient history
- Add prescriptions

### 👩‍⚕️ Nurse
- Nurse dashboard
- Update patient information
- Add and update patient vitals

### 💊 Pharmacist
- Pharmacist dashboard

### 🧑‍🤝‍🧑 Patient
- Patient registration and login
- Patient dashboard
- Book appointments
- View prescriptions

## 🛠️ Technologies Used

- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript
- Jinja2
- Git & GitHub

## 📂 Project Structure

```text
Healthcare-management-system/
│
├── app.py
├── check_db.py
├── healthcare.db
├── .gitignore
├── README.md
│
├── static/
│   └── css/
│       ├── js/
│       │   └── script.js
│       └── style.css
│
└── templates/
    ├── admin/
    ├── doctor/
    ├── nurse/
    ├── patient/
    ├── pharmacist/
    ├── base.html
    ├── login.html
    └── register.html
