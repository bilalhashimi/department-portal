#!/bin/sh

# Wait for database to be ready
echo "Waiting for database..."
while ! python manage.py dbshell > /dev/null 2>&1; do
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

# Collect static files
python manage.py collectstatic --noinput

# Start server
echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000 