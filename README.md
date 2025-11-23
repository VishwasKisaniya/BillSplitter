# Bill Splitter App

A web application to split bills among friends, track payments, and send UPI payment requests.
# Deployed URL:
https://billsplitter-yzhj.onrender.com

## Features

- User registration and authentication
- Create groups with friends
- Add bills to groups
- Split bills equally or custom amounts
- Track who has paid and who still owes money
- UPI payment integration with QR codes
- Mobile-friendly design

## Tech Stack

- Django web framework
- SQLite (local development) / PostgreSQL (production)
- Bootstrap 5 for responsive design
- UPI payment integration

## Local Development Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/bill-splitter.git
cd bill-splitter
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run migrations:
```
python manage.py migrate
```

5. Create a superuser (optional):
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## Deployment on Render

1. Create a new Web Service on Render
2. Link to your GitHub repository
3. Use these settings:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn splitter.wsgi:application`
   - **Environment Variables**:
     - `SECRET_KEY`: [Generate a secure key]
     - `DEBUG`: False
     - `ALLOWED_HOSTS`: yourdomain.onrender.com
4. Add a PostgreSQL database and Render will automatically set the DATABASE_URL
5. Deploy!

## License

MIT 
