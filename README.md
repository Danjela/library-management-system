# 📚 Library Management System (Django + DRF)

This project is a **Library Management System backend** built with **Django** and **Django REST Framework**. It focuses on **clean architecture**, **clear domain rules**, and **real-world behaviors** such as borrowing, returning, reservations, permissions, and logging.

---

## 🚀 What This Project Does

### Core Features

* User registration, login, logout (JWT-based)
* Role-based access control:

  * **MEMBER** – can browse, borrow, return, reserve books
  * **LIBRARIAN** – can manage books and copies
* Book management with multiple physical copies
* Borrowing & returning logic with rules
* Book reservations
* Pagination, ordering, and filtering
* Soft deletion for books
* Structured logging (request + domain logs)
* Clean separation of concerns (services, serializers, permissions)

---

## 🧱 Architecture Overview

The project follows:

```
API (Views)
   ↓
Serializers (Validation)
   ↓
Services (Business Logic)
   ↓
Models (Persistence)

---

## 📂 Project Structure

```
library_project/
├── config/             # Django project settings
├── users/              # Authentication, roles, permissions
├── library/            # Books, authors, copies, members, borrowing & returning, reservations
├── manage.py
└── requirements.txt
```

---

## 🧑‍💻 Roles & Permissions

### MEMBER

* View available books
* Search books (title, author)
* Borrow books
* Return own borrowed books
* Reserve books

### LIBRARIAN

* Create, update, delete books
* Manage book copies
* View detailed book inventory

Permissions are enforced using **DRF permission classes** and **object-level checks**.

---

## 🔐 Authentication

* JWT-based authentication
* Django `User` model
* Library-specific `Member` model linked to `User`
* Roles implemented using Django **Groups**

---

## 📝 Logging

* Logs are written using Python's `logging` module
* Structured JSON logs
* Includes request logs and domain events

---

## 🧪 Testing

The project includes tests for:

* Borrowing logic
* Returning logic

Tests are written using **pytest** and **pytest-django**.

---

## ⚙️ How to Set Up the Project

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Danjela/library-management-system.git
cd library-management-system
```

---

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Apply database migrations

```bash
python manage.py migrate
```

---

### 6️⃣ Create a superuser

```bash
python manage.py createsuperuser
```

A superuser can assign librarian roles.

---

### 7️⃣ Run the development server

```bash
python manage.py runserver
```

API will be available at:

```
http://127.0.0.1:8000/
```

---

## 🧪 Running Tests

```bash
pytest
```

---
