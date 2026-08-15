import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

print("Connecting to CockroachDB...")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

print("Creating tables...")

# Create users table
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email STRING UNIQUE NOT NULL,
    phone STRING,
    full_name STRING,
    country STRING DEFAULT 'Morocco',
    city STRING DEFAULT 'Casablanca',
    language STRING DEFAULT 'en',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
''')

# Create user_preferences table
cur.execute('''
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preference_type STRING NOT NULL,
    preference_key STRING NOT NULL,
    preference_value STRING NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    source STRING DEFAULT 'user_input',
    is_active BOOL DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE (user_id, preference_type, preference_key)
);
''')

# Create conversations table
cur.execute('''
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id STRING NOT NULL,
    message_role STRING NOT NULL,
    message_text STRING NOT NULL,
    intent STRING,
    entities JSONB,
    sentiment STRING DEFAULT 'neutral',
    created_at TIMESTAMP DEFAULT now()
);
''')

# Create bookings table
cur.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    booking_type STRING NOT NULL,
    service_provider STRING,
    from_location STRING,
    to_location STRING,
    departure_date DATE,
    return_date DATE,
    amount DECIMAL(10,2),
    currency STRING DEFAULT 'MAD',
    status STRING DEFAULT 'pending',
    pnr_code STRING,
    booking_details JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
''')

# Create services table
cur.execute('''
CREATE TABLE IF NOT EXISTS services (
    service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name STRING NOT NULL UNIQUE,
    service_category STRING NOT NULL,
    set_number INT NOT NULL,
    screen_number INT NOT NULL,
    api_endpoint STRING,
    is_active BOOL DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);
''')

# Create ai_memory_context table
cur.execute('''
CREATE TABLE IF NOT EXISTS ai_memory_context (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    memory_summary STRING NOT NULL,
    memory_vector BYTES,
    last_accessed TIMESTAMP DEFAULT now(),
    access_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (user_id)
);
''')

print("Tables created successfully!")

# Insert 36 services
services_data = [
    ('AI Chat Assistant', 'ai', 1, 1, '/api/v1/chat'),
    ('Flight Search', 'transport', 1, 2, '/api/v1/flights/search'),
    ('Train Search', 'transport', 1, 3, '/api/v1/trains/search'),
    ('Bus Search', 'transport', 1, 4, '/api/v1/bus/search'),
    ('Taxi / Ride Hailing', 'transport', 1, 5, '/api/v1/taxi/search'),
    ('Hotel Search', 'accommodation', 1, 6, '/api/v1/hotels/search'),
    ('Car Rental', 'transport', 1, 7, '/api/v1/cars/search'),
    ('My Bookings', 'account', 1, 8, '/api/v1/bookings'),
    ('Travel Insurance', 'service', 1, 9, '/api/v1/insurance'),
    ('Flight Booking', 'booking', 2, 1, '/api/v1/flights/book'),
    ('Train Booking', 'booking', 2, 2, '/api/v1/trains/book'),
    ('Hotel Booking', 'booking', 2, 3, '/api/v1/hotels/book'),
    ('Payment Gateway', 'payment', 2, 4, '/api/v1/payments/process'),
    ('Booking History', 'account', 2, 5, '/api/v1/bookings/history'),
    ('Cancel Booking', 'booking', 2, 6, '/api/v1/bookings/cancel'),
    ('Modify Booking', 'booking', 2, 7, '/api/v1/bookings/modify'),
    ('Refund Status', 'payment', 2, 8, '/api/v1/payments/refund'),
    ('Invoice Generator', 'service', 2, 9, '/api/v1/invoices'),
    ('Profile Settings', 'account', 3, 1, '/api/v1/users/profile'),
    ('Preferences', 'account', 3, 2, '/api/v1/users/preferences'),
    ('Language Settings', 'account', 3, 3, '/api/v1/users/language'),
    ('Currency Converter', 'tool', 3, 4, '/api/v1/tools/currency'),
    ('Travel Documents', 'service', 3, 5, '/api/v1/documents'),
    ('Emergency Contacts', 'service', 3, 6, '/api/v1/emergency'),
    ('Weather Forecast', 'tool', 3, 7, '/api/v1/tools/weather'),
    ('Local Guides', 'service', 3, 8, '/api/v1/guides'),
    ('Reviews & Ratings', 'service', 3, 9, '/api/v1/reviews'),
    ('Smart Recommendations', 'ai', 4, 1, '/api/v1/ai/recommend'),
    ('Price Alerts', 'ai', 4, 2, '/api/v1/ai/alerts'),
    ('Trip Planner', 'ai', 4, 3, '/api/v1/ai/planner'),
    ('Budget Tracker', 'ai', 4, 4, '/api/v1/ai/budget'),
    ('Carbon Footprint', 'ai', 4, 5, '/api/v1/ai/carbon'),
    ('Travel Checklist', 'ai', 4, 6, '/api/v1/ai/checklist'),
    ('Translation Tool', 'ai', 4, 7, '/api/v1/ai/translate'),
    ('Voice Assistant', 'ai', 4, 8, '/api/v1/ai/voice'),
    ('Help & Support', 'ai', 4, 9, '/api/v1/support')
]

print("Inserting 36 services...")
for service in services_data:
    try:
        cur.execute('''
            INSERT INTO services (service_name, service_category, set_number, screen_number, api_endpoint)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (service_name) DO NOTHING
        ''', service)
    except Exception as e:
        print(f"Warning: {e}")

print("Services inserted!")

# Insert demo user
print("Inserting demo user...")
cur.execute('''
    INSERT INTO users (email, full_name, phone, country, city, language)
    VALUES ('demo@safar.ai', 'Sara ZEROUAL', '+212600000000', 'Morocco', 'Casablanca', 'en')
    ON CONFLICT (email) DO NOTHING
''')

# Insert demo preferences
print("Inserting demo preferences...")
cur.execute('''
    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source)
    SELECT user_id, 'budget', 'max_budget_eur', '500', 'user_input' FROM users WHERE email = 'demo@safar.ai'
    ON CONFLICT DO NOTHING
''')

cur.execute('''
    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source)
    SELECT user_id, 'transport', 'preferred_class', 'economy_plus', 'user_input' FROM users WHERE email = 'demo@safar.ai'
    ON CONFLICT DO NOTHING
''')

cur.execute('''
    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source)
    SELECT user_id, 'diet', 'dietary_restrictions', 'vegetarian', 'user_input' FROM users WHERE email = 'demo@safar.ai'
    ON CONFLICT DO NOTHING
''')

cur.execute('''
    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source)
    SELECT user_id, 'seat', 'preferred_seat', 'window', 'user_input' FROM users WHERE email = 'demo@safar.ai'
    ON CONFLICT DO NOTHING
''')

cur.execute('''
    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source)
    SELECT user_id, 'transport', 'avoid_layovers', 'true', 'ai_inferred' FROM users WHERE email = 'demo@safar.ai'
    ON CONFLICT DO NOTHING
''')

print("Demo data inserted!")

cur.close()
conn.close()
print("\n✅ DATABASE INITIALIZED SUCCESSFULLY!")
print("You can now test: http://127.0.0.1:5000/api/v1/services")
