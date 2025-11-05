from flask import Flask, send_file, request
from peewee import *
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import io
import time
from collections import defaultdict
import re

app = Flask(__name__)

# Database setup
db = SqliteDatabase('profiles.db')

# Database model
class Profile(db.Model):
    username = CharField()
    addr = CharField()
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = db

# Create tables
try:
    db.connect()
    db.create_tables([Profile], safe=True)
except Exception as e:
    print(f"Database error: {e}")

# Rate limiting implementation
rate_limits = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 30

def is_rate_limited(ip_address):
    """Check if an IP is rate limited"""
    now = time.time()
    # Remove requests older than 1 minute
    rate_limits[ip_address] = [req_time for req_time in rate_limits[ip_address] if now - req_time < 60]
    
    # Check if limit exceeded
    if len(rate_limits[ip_address]) >= MAX_REQUESTS_PER_MINUTE:
        return True
    
    # Add current request
    rate_limits[ip_address].append(now)
    return False

# Security: Validate username format
def is_valid_username(username):
    """Validate username format to prevent injection attacks"""
    # Allow only alphanumeric characters, underscores, and hyphens
    return re.match("^[a-zA-Z0-9_-]+$", username) is not None

# Create image function
def create_profile_image(download_count):
    # Create a larger image to accommodate the text
    img = Image.new('RGB', (100, 20), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw the text centered
    text = str(download_count)
    text_width = len(text) * 6  # Approximate width (6 pixels per character)
    text_x = (100 - text_width) // 2
    draw.text((text_x, 0), text, fill=(0, 0, 0))
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def get_unique_ips_count(username, start_date, end_date):
    """Get unique IP count with proper SQL escaping"""
    # Validate username to prevent injection
    if not is_valid_username(username):
        return 0
    
    # Use parameterized queries to prevent SQL injection
    try:
        query = (Profile
                 .select(fn.COUNT(fn.DISTINCT(Profile.addr)).alias('count'))
                 .where((Profile.username == username) &
                        (Profile.created_at >= start_date) &
                        (Profile.created_at < end_date))
                 .scalar())
        return query if query is not None else 0
    except Exception as e:
        print(f"Database query error: {e}")
        return 0

@app.route('/<username>/last_month')
def get_profile_image_last_month(username):
    # Validate username
    if not is_valid_username(username):
        return "Invalid username", 400
    
    # Check rate limiting
    ip_address = request.remote_addr
    if is_rate_limited(ip_address):
        return "Rate limit exceeded. Please try again later.", 429
    
    # Get current time
    now = datetime.now()
    
    # Calculate the start of last month
    if now.month == 1:
        start_date = now.replace(year=now.year - 1, month=12)
    else:
        start_date = now.replace(month=now.month - 1)
    
    # Calculate the end of last month
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    
    # Count unique IP addresses for this period
    unique_ips_count = get_unique_ips_count(username, start_date, end_date)
    
    # Create and return image with unique IP count
    img_bytes = create_profile_image(unique_ips_count)
    
    # Log the access - create a new record every time
    try:
        # Validate IP address
        if not ip_address:
            ip_address = "unknown"
        Profile.create(username=username, addr=ip_address)
    except Exception as e:
        print(f"Error creating database record: {e}")
    
    return send_file(img_bytes, mimetype='image/png')

@app.route('/<username>/last_week')
def get_profile_image_last_week(username):
    # Validate username
    if not is_valid_username(username):
        return "Invalid username", 400
    
    # Check rate limiting
    ip_address = request.remote_addr
    if is_rate_limited(ip_address):
        return "Rate limit exceeded. Please try again later.", 429
    
    # Get current time
    now = datetime.now()
    
    # Calculate the start of last week (Monday)
    days_since_monday = now.weekday()
    start_date = now - timedelta(days=days_since_monday + 7)
    
    # Calculate the end of last week (Sunday)
    end_date = start_date + timedelta(days=7)
    
    # Count unique IP addresses for this period
    unique_ips_count = get_unique_ips_count(username, start_date, end_date)
    
    # Create and return image with unique IP count
    img_bytes = create_profile_image(unique_ips_count)
    
    # Log the access - create a new record every time
    try:
        # Validate IP address
        if not ip_address:
            ip_address = "unknown"
        Profile.create(username=username, addr=ip_address)
    except Exception as e:
        print(f"Error creating database record: {e}")
    
    return send_file(img_bytes, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
