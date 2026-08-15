-- ============================================================
-- SAFAR AI - COCKROACHDB SCHEMA
-- Backend Database Layer for CockroachDB x AWS Hackathon
-- Agentic Memory Implementation
-- ============================================================

-- 1. USERS TABLE
-- Stores user profiles and authentication data
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

-- 2. AGENTIC MEMORY - USER PREFERENCES
-- Core table for the hackathon: AI remembers user preferences across sessions
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preference_type STRING NOT NULL,  -- 'budget', 'transport', 'diet', 'seat', 'payment'
    preference_key STRING NOT NULL,     -- 'max_budget', 'preferred_class', 'dietary_restrictions'
    preference_value STRING NOT NULL,   -- '500', 'business', 'vegetarian'
    confidence_score DECIMAL(3,2) DEFAULT 1.00,  -- AI confidence in this memory
    source STRING DEFAULT 'user_input', -- 'user_input', 'ai_inferred', 'booking_history'
    is_active BOOL DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    INDEX idx_user_preferences (user_id, preference_type),
    INDEX idx_active_preferences (user_id, is_active)
);

-- 3. AI CONVERSATION MEMORY
-- Stores all AI chat history with context for persistent memory
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id STRING NOT NULL,       -- Groups messages by session
    message_role STRING NOT NULL,       -- 'user' or 'assistant'
    message_text STRING NOT NULL,
    intent STRING,                     -- 'flight_search', 'booking', 'general', 'preference_update'
    entities JSONB,                    -- Extracted entities: {"destination": "Paris", "budget": 500}
    sentiment STRING DEFAULT 'neutral', -- 'positive', 'neutral', 'negative'
    created_at TIMESTAMP DEFAULT now(),
    INDEX idx_user_conversations (user_id, created_at DESC),
    INDEX idx_session (session_id)
);

-- 4. BOOKINGS (Flights, Trains, Hotels, etc.)
CREATE TABLE IF NOT EXISTS bookings (
    booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    booking_type STRING NOT NULL,      -- 'flight', 'train', 'hotel', 'taxi', 'bus'
    service_provider STRING,           -- 'Royal Air Maroc', 'ONCF', etc.
    from_location STRING,
    to_location STRING,
    departure_date DATE,
    return_date DATE,
    amount DECIMAL(10,2),
    currency STRING DEFAULT 'MAD',
    status STRING DEFAULT 'pending',   -- 'pending', 'confirmed', 'cancelled', 'completed'
    pnr_code STRING,                   -- Passenger Name Record
    booking_details JSONB,             -- Flexible storage for all booking data
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    INDEX idx_user_bookings (user_id, created_at DESC),
    INDEX idx_booking_status (status)
);

-- 5. SERVICES CATALOG (The 36 services)
CREATE TABLE IF NOT EXISTS services (
    service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name STRING NOT NULL UNIQUE,
    service_category STRING NOT NULL,  -- 'transport', 'accommodation', 'food', 'entertainment'
    set_number INT NOT NULL,           -- 1 to 4
    screen_number INT NOT NULL,      -- 1 to 9 within each set
    api_endpoint STRING,               -- Backend API route for this service
    is_active BOOL DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);

-- 6. AI MEMORY CONTEXT (For Bedrock Integration)
-- Stores processed memory summaries that the AI uses for recommendations
CREATE TABLE IF NOT EXISTS ai_memory_context (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    memory_summary STRING NOT NULL,    -- "User prefers direct flights under 500€, vegetarian meals, window seats"
    memory_vector BYTES,               -- For future vector search (CockroachDB Vector Indexing)
    last_accessed TIMESTAMP DEFAULT now(),
    access_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    INDEX idx_user_memory (user_id)
);

-- ============================================================
-- INITIAL DATA: Populate the 36 services of Safar AI
-- ============================================================

INSERT INTO services (service_name, service_category, set_number, screen_number, api_endpoint) VALUES
-- Set 1: Core Travel Services
('AI Chat Assistant', 'ai', 1, 1, '/api/v1/chat'),
('Flight Search', 'transport', 1, 2, '/api/v1/flights/search'),
('Train Search', 'transport', 1, 3, '/api/v1/trains/search'),
('Bus Search', 'transport', 1, 4, '/api/v1/bus/search'),
('Taxi / Ride Hailing', 'transport', 1, 5, '/api/v1/taxi/search'),
('Hotel Search', 'accommodation', 1, 6, '/api/v1/hotels/search'),
('Car Rental', 'transport', 1, 7, '/api/v1/cars/search'),
('My Bookings', 'account', 1, 8, '/api/v1/bookings'),
('Travel Insurance', 'service', 1, 9, '/api/v1/insurance'),

-- Set 2: Booking & Payments
('Flight Booking', 'booking', 2, 1, '/api/v1/flights/book'),
('Train Booking', 'booking', 2, 2, '/api/v1/trains/book'),
('Hotel Booking', 'booking', 2, 3, '/api/v1/hotels/book'),
('Payment Gateway', 'payment', 2, 4, '/api/v1/payments/process'),
('Booking History', 'account', 2, 5, '/api/v1/bookings/history'),
('Cancel Booking', 'booking', 2, 6, '/api/v1/bookings/cancel'),
('Modify Booking', 'booking', 2, 7, '/api/v1/bookings/modify'),
('Refund Status', 'payment', 2, 8, '/api/v1/payments/refund'),
('Invoice Generator', 'service', 2, 9, '/api/v1/invoices'),

-- Set 3: User Services
('Profile Settings', 'account', 3, 1, '/api/v1/users/profile'),
('Preferences', 'account', 3, 2, '/api/v1/users/preferences'),
('Language Settings', 'account', 3, 3, '/api/v1/users/language'),
('Currency Converter', 'tool', 3, 4, '/api/v1/tools/currency'),
('Travel Documents', 'service', 3, 5, '/api/v1/documents'),
('Emergency Contacts', 'service', 3, 6, '/api/v1/emergency'),
('Weather Forecast', 'tool', 3, 7, '/api/v1/tools/weather'),
('Local Guides', 'service', 3, 8, '/api/v1/guides'),
('Reviews & Ratings', 'service', 3, 9, '/api/v1/reviews'),

-- Set 4: AI & Smart Features
('Smart Recommendations', 'ai', 4, 1, '/api/v1/ai/recommend'),
('Price Alerts', 'ai', 4, 2, '/api/v1/ai/alerts'),
('Trip Planner', 'ai', 4, 3, '/api/v1/ai/planner'),
('Budget Tracker', 'ai', 4, 4, '/api/v1/ai/budget'),
('Carbon Footprint', 'ai', 4, 5, '/api/v1/ai/carbon'),
('Travel Checklist', 'ai', 4, 6, '/api/v1/ai/checklist'),
('Translation Tool', 'ai', 4, 7, '/api/v1/ai/translate'),
('Voice Assistant', 'ai', 4, 8, '/api/v1/ai/voice'),
('Help & Support', 'ai', 4, 9, '/api/v1/support')
ON CONFLICT (service_name) DO NOTHING;

-- ============================================================
-- SAMPLE DATA: Demo user with Agentic Memory
-- ============================================================

INSERT INTO users (email, full_name, phone, country, city, language) VALUES
('demo@safar.ai', 'Sara ZEROUAL', '+212600000000', 'Morocco', 'Casablanca', 'en')
ON CONFLICT (email) DO NOTHING;

-- Insert sample preferences (Agentic Memory)
INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, source) 
SELECT user_id, 'budget', 'max_budget_eur', '500', 'user_input' FROM users WHERE email = 'demo@safar.ai'
UNION ALL
SELECT user_id, 'transport', 'preferred_class', 'economy_plus', 'user_input' FROM users WHERE email = 'demo@safar.ai'
UNION ALL
SELECT user_id, 'diet', 'dietary_restrictions', 'vegetarian', 'user_input' FROM users WHERE email = 'demo@safar.ai'
UNION ALL
SELECT user_id, 'seat', 'preferred_seat', 'window', 'user_input' FROM users WHERE email = 'demo@safar.ai'
UNION ALL
SELECT user_id, 'transport', 'avoid_layovers', 'true', 'ai_inferred' FROM users WHERE email = 'demo@safar.ai'
ON CONFLICT DO NOTHING;
