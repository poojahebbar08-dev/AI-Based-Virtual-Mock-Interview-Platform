# AI-Based Virtual Mock Interview Platform

An AI-powered mock interview platform built with Django. This platform provides candidates with a comprehensive environment to practice interviews, featuring both AI-driven mock interviews and live video sessions with HR professionals.

## 🌟 Key Features

- **Candidate Dashboard**: A centralized hub for candidates to manage their interview preparations.
- **AI Mock Interviews**: Leverages NLP (NLTK) to analyze and provide feedback on candidate responses.
- **HR Video Interviews**: Live 1-on-1 video interviews with HR professionals seamlessly integrated using Jitsi Meet.
- **Email Verification**: Secure authentication system with OTP-based email verification.
- **HR Dashboard**: A dedicated interface for HR professionals to manage and conduct scheduled interviews.

## 🛠️ Technology Stack

- **Backend**: Python, Django
- **Database**: SQLite (Development)
- **Video Conferencing**: Jitsi Meet integration
- **NLP**: NLTK (Natural Language Toolkit)
- **Frontend**: HTML, CSS, JavaScript (Django Templates)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository** (or download the source code)
2. **Navigate to the project directory**
   ```bash
   cd ai_interview_platform-main
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up NLTK resources**
   ```bash
   python nltk_setup.py
   ```
5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```
6. **Create a superuser (optional, for admin access)**
   ```bash
   python manage.py createsuperuser
   ```
7. **Run the development server**
   ```bash
   python manage.py runserver
   ```
8. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## 📧 Email Configuration

To enable the email confirmation and OTP features, you need to configure your SMTP settings. 

Please refer to the [Email Setup Guide](EMAIL_SETUP.md) for detailed instructions on configuring your Gmail App Password and updating the `settings.py` file.

## 🎥 HR Video Interviews

The platform supports live video interviews between candidates and HR professionals without requiring additional software installations.

For detailed instructions on scheduling, joining, and managing live HR interviews, please refer to the [HR Interview Usage Guide](HR_INTERVIEW_USAGE_GUIDE.md).

## 📁 Project Structure

- `ai_interview_platform/` - Main Django project configuration folder
- `candidate/` - App handling candidate profiles, mock interviews, and dashboard
- `hr/` - App handling HR professional features and interview management
- `adminpanel/` - Custom administrative controls and overview
- `media/` & `static/` - User uploads and static assets (CSS, JS, Images)
- `templates/` - HTML templates for the frontend

## 📄 License

This project is open-source and available for educational and developmental purposes.
