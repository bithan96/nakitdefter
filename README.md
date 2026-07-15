# NakitDefter

A personal budget and expense tracking web application built with Flask.

![Dashboard Demo](Desktop/NakitDefter.gif)

## Features
- Email OTP verification on signup (via Brevo API)
- Secure authentication with hashed passwords and session management
- Dashboard with income/expense tracking and visual analytics
- Bank account linking
- Profile photo upload
- Password reset via email verification

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite
- **Email Service:** Brevo API
- **Frontend:** HTML, CSS, Jinja2

## Getting Started

1. Clone the repository
```bash
git clone https://github.com/bithan96/nakitdefter.git
cd nakitdefter
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root folder with:
BREVO_API_KEY=your_brevo_api_key
SENDER_EMAIL=your_sender_email
SECRET_KEY=your_random_secret_key
4. Run the app
```bash
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser

## Author
Bitanya — [GitHub](https://github.com/bithan96)