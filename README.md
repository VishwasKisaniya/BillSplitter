# Bill Splitter App

A web application to split bills among friends and groups, built with Django.

## Features

- User authentication and registration with phone numbers
- Create groups with friends using their phone numbers
- Add bills to groups and split them equally or with custom amounts
- Track balances with friends
- Payment simulation with redirects to payment methods (Amazon Pay, Google Pay, Paytm, etc.)
- Dashboard to view all bills, groups, and balances

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```
4. Create a superuser:
   ```
   python3 manage.py createsuperuser
   ```
5. Run the development server:
   ```
   python3 manage.py runserver
   ```

## Usage

1. Register with your phone number
2. Create a group and add friends using their phone numbers
3. Create a bill and choose how to split it
4. View your balances with friends
5. Pay your bills by selecting a payment method

## Technology Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, Bootstrap 5
- **Database**: SQLite (default Django database)
- **Forms**: django-crispy-forms with Bootstrap 5 