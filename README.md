# Application Tracking System

An Application Tracking System (ATS) designed to streamline the process of managing, tracking, and reviewing job applications. Built using Python and TypeScript, this project aims to help organizations and recruiters efficiently monitor candidate progress from application submission to final decision.

## Features

- **Candidate Management:** Add, update, and manage candidate profiles and resumes.
- **Job Posting:** Create and publish job postings for open positions.
- **Application Tracking:** Track applications by status (applied, in review, interviewed, offered, rejected, etc.).
- **Interview Scheduling:** Schedule and manage interviews with candidates.
- **Feedback & Notes:** Collect feedback from interviewers and maintain notes on candidates.
- **Dashboard:** Visualize key metrics and monitor recruitment pipeline.
- **Role-Based Access:** Different access for recruiters, hiring managers, and admins.
- **Notifications:** Email or in-app notifications for application updates and interview scheduling.

## Tech Stack

- **Backend:** Python (likely using a framework like Django or Flask)
- **Frontend:** TypeScript (potentially React, Angular, or Vue)
- **Other:** Docker for containerization

## Getting Started

### Prerequisites

- Python 3.x
- Node.js and npm
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```sh
   git clone https://github.com/salmansrizon/application_tracking_system.git
   cd application_tracking_system
   ```

2. **Backend Setup**
   - Create a virtual environment:
     ```sh
     python -m venv venv
     source venv/bin/activate
     ```
   - Install dependencies:
     ```sh
     pip install -r requirements.txt
     ```
   - Run migrations (if using Django/Flask-Migrate):
     ```sh
     python manage.py migrate
     ```
   - Start the backend server:
     ```sh
     python manage.py runserver
     ```

3. **Frontend Setup**
   - Navigate to the frontend directory:
     ```sh
     cd frontend
     ```
   - Install dependencies:
     ```sh
     npm install
     ```
   - Start the frontend development server:
     ```sh
     npm start
     ```

4. **Docker Deployment (Optional)**
   - Build and run with Docker:
     ```sh
     docker-compose up --build
     ```

## Folder Structure

```
application_tracking_system/
│
├── backend/                # Python backend source code
├── frontend/               # TypeScript frontend source code
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── ...
```

## Contributing

1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a pull request.

## License

This project is licensed under the MIT License.

## Contact

Created by [@salmansrizon](https://github.com/salmansrizon) - feel free to reach out!
