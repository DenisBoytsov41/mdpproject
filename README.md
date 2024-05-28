If you want to generate a JSON file with a schedule, run the file startJSON.py

If you get ical format based on a JSON file, run startCreateCAL.py

If everything is done at once scriptStart.py

cd /var/www/html

uwsgi --socket 127.0.0.1:8080 --module flash_app:app --processes 4 --threads 2 --stats 127.0.0.1:9191

netstat -ano | findstr :8080

taskkill /F /PID YOUR_PID

sudo ln -s /etc/nginx/sites-available/your_config/etc/nginx/sites-enabled/

