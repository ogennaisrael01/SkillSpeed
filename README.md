# Skill Speed Backend API

## Project Overview

**Skill Speed** is a backend API built with **Django REST Framework (DRF)**. The platform is designed to expose **children between the ages of 5 and 15** to **technology, craft, and vocational skills** through structured learning paths.

The system provides age-appropriate skill paths, controlled access to learning content, and progress tracking to ensure a safe and guided learning experience for young learners.

---

## Core Features

* Age-based skill path access (5–15 years)
* Structured learning paths and skills
* Lesson-based content delivery
* Enrollment-controlled content access
* Progress tracking per lesson and skill
* Scalable and API-first architecture

---

## How the Platform Works
1. Guardian register on the platform
2. onboard child and authomantically child is registered on the platform
3. Children register on the platform (or are registered by a parent/admin)
4. Skill paths are filtered based on age eligibility
5. Children enroll in a skill path
6. Enrolled users gain access to skills and lessons
7. Progress is tracked automatically as lessons are completed
8. Child can get recommendation based on age, interest.

---

## Technology Stack

* **Python**
* **Django**
* **Django REST Framework (DRF)**
* **REST APIs**
* **REDIS**
* **CELERY** **
* **GEMENI**
* **Docker**
* **CI/CD Pipelines**

---

## Backend Concepts Applied

* Relational database design
* API-first architecture
* Asynchronous programming concepts
* Caching strategies for performance
* Clean separation of concerns

---

## How to Run the Application

### Prerequisites

* Python 3.10+
* pip
* Virtualenv (recommended)

### Run Locally

1. Clone the repository

   ```bash
   git clone <repository-url>
   cd skill-speed-backend
   ```

2. Create and activate a virtual environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations

   ```bash
   python manage.py migrate
   ```

5. Start the development server

   ```bash
   python manage.py runserver
   ```

6. Access the application

   * API Base URL: `http://127.0.0.1:8000/`
   * Admin Panel: `http://127.0.0.1:8000/admin/`
   * Swagger Documentation: `https://127.0.0.1:8000/docs/`

---

## Project Status

🚧 **In Development**


## License

This project is built for learning and portfolio demonstration purposes.

## Contact
`ogennaisrael@gmail.com` **LET'S WORK TOGETHER**
