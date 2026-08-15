# ============================================================
# SAFAR AI - BACKEND API
# Python Flask Backend for CockroachDB x AWS Hackathon
# Agentic Memory Implementation
# Author: Sara ZEROUAL (Backend Logic Development)
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
import json

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# ============================================================
# DATABASE CONFIGURATION
# Replace with your CockroachDB connection string
# Format: postgresql://username:password@host:port/database?sslmode=require
# ============================================================
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://demo:demo123@localhost:26257/safar_ai?sslmode=require'
)

def get_db_connection():
    """Create and return a database connection to CockroachDB"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint for AWS Lambda / API Gateway"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT version()')
            version = cur.fetchone()
            db_version = version[0] if version else "Unknown"
        return jsonify({
            'status': 'healthy',
            'database': 'CockroachDB',
            'version': db_version,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# ============================================================
# 1. USER MANAGEMENT
# ============================================================

@app.route('/api/v1/users/register', methods=['POST'])
def register_user():
    """Register a new user"""
    data = request.get_json()
    email = data.get('email')
    full_name = data.get('full_name')
    phone = data.get('phone')
    country = data.get('country', 'Morocco')
    city = data.get('city', 'Casablanca')
    language = data.get('language', 'en')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (email, full_name, phone, country, city, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING user_id, email, created_at
            ''', (email, full_name, phone, country, city, language))
            user = cur.fetchone()
            conn.commit()

        if not user:
            return jsonify({'success': False, 'error': 'Failed to register user'}), 500

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'user_id': str(user[0]),
                'email': user[1],
                'created_at': user[2].isoformat()
            }
        }), 201
    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already exists'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/v1/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile with all agentic memory"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get user basic info
            cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cur.fetchone()

            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            # Get all active preferences (AGENTIC MEMORY)
            cur.execute('''
                SELECT preference_type, preference_key, preference_value, 
                       confidence_score, source, updated_at
                FROM user_preferences 
                WHERE user_id = %s AND is_active = true
                ORDER BY preference_type, updated_at DESC
            ''', (user_id,))
            preferences = cur.fetchall()

            # Get AI memory context
            cur.execute('''
                SELECT memory_summary, last_accessed, access_count
                FROM ai_memory_context
                WHERE user_id = %s
                ORDER BY last_accessed DESC
                LIMIT 1
            ''', (user_id,))
            memory = cur.fetchone()

        return jsonify({
            'success': True,
            'user': dict(user),
            'agentic_memory': {
                'preferences': [dict(p) for p in preferences],
                'total_preferences': len(preferences),
                'ai_context': dict(memory) if memory else None
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============================================================
# 2. AGENTIC MEMORY - CORE FEATURE FOR HACKATHON
# ============================================================

@app.route('/api/v1/users/<user_id>/preferences', methods=['POST'])
def save_preference(user_id):
    """Save or update a user preference (Agentic Memory)"""
    data = request.get_json()
    preference_type = data.get('preference_type')  # 'budget', 'transport', 'diet', etc.
    preference_key = data.get('preference_key')    # 'max_budget', 'preferred_class'
    preference_value = data.get('preference_value') # '500', 'business'
    source = data.get('source', 'user_input')        # 'user_input', 'ai_inferred'
    confidence = data.get('confidence_score', 1.00)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Upsert: update if exists, insert if new
            cur.execute('''
                INSERT INTO user_preferences 
                    (user_id, preference_type, preference_key, preference_value, source, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, preference_type, preference_key) 
                DO UPDATE SET 
                    preference_value = EXCLUDED.preference_value,
                    source = EXCLUDED.source,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = now(),
                    is_active = true
                RETURNING preference_id, created_at, updated_at
            ''', (user_id, preference_type, preference_key, preference_value, source, confidence))

            result = cur.fetchone()
            
            if not result:
                raise Exception("Failed to save preference.")

            # Update AI memory context
            update_ai_memory_context(user_id, cur)
            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Preference saved to Agentic Memory',
            'preference_id': str(result[0]),
            'timestamp': result[2].isoformat()
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/v1/users/<user_id>/preferences', methods=['GET'])
def get_preferences(user_id):
    """Retrieve all active preferences for a user (Agentic Memory recall)"""
    preference_type = request.args.get('type')  # Optional filter

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if preference_type:
                cur.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = %s AND preference_type = %s AND is_active = true
                    ORDER BY updated_at DESC
                ''', (user_id, preference_type))
            else:
                cur.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = %s AND is_active = true
                    ORDER BY preference_type, updated_at DESC
                ''', (user_id,))

            preferences = cur.fetchall()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'preferences': [dict(p) for p in preferences],
            'count': len(preferences)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


def update_ai_memory_context(user_id, cursor):
    """Generate AI memory summary from all preferences"""
    cursor.execute('''
        SELECT preference_type, preference_key, preference_value
        FROM user_preferences
        WHERE user_id = %s AND is_active = true
        ORDER BY preference_type
    ''', (user_id,))
    prefs = cursor.fetchall()

    # Build memory summary
    memory_parts = []
    for p in prefs:
        memory_parts.append(f"{p[1]}: {p[2]}")

    summary = "User profile: " + "; ".join(memory_parts) if memory_parts else "New user, no preferences yet."

    cursor.execute('''
        INSERT INTO ai_memory_context (user_id, memory_summary, access_count)
        VALUES (%s, %s, 1)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            memory_summary = EXCLUDED.memory_summary,
            last_accessed = now(),
            access_count = ai_memory_context.access_count + 1
    ''', (user_id, summary))


# ============================================================
# 3. AI CHAT WITH MEMORY
# ============================================================

@app.route('/api/v1/chat', methods=['POST'])
def chat_with_ai():
    """AI Chat endpoint with Agentic Memory retrieval"""
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    session_id = data.get('session_id', 'default')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. RETRIEVE AGENTIC MEMORY
            cur.execute('''
                SELECT preference_type, preference_key, preference_value
                FROM user_preferences
                WHERE user_id = %s AND is_active = true
            ''', (user_id,))
            memory = cur.fetchall()

            # 2. RETRIEVE CONVERSATION HISTORY
            cur.execute('''
                SELECT message_role, message_text, entities, created_at
                FROM conversations
                WHERE user_id = %s AND session_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id, session_id))
            history = cur.fetchall()

            # 3. SAVE USER MESSAGE
            cur.execute('''
                INSERT INTO conversations (user_id, session_id, message_role, message_text, intent)
                VALUES (%s, %s, 'user', %s, 'general')
                RETURNING conversation_id
            ''', (user_id, session_id, message))

            # 4. GENERATE AI RESPONSE (integrated with AWS Bedrock + safe fallback)
            memory_context = ", ".join([f"{m['preference_key']}={m['preference_value']}" for m in memory])

            ai_response = generate_ai_response(message, memory_context, history)

            # 5. SAVE AI RESPONSE
            cur.execute('''
                INSERT INTO conversations (user_id, session_id, message_role, message_text, intent)
                VALUES (%s, %s, 'assistant', %s, 'general')
            ''', (user_id, session_id, ai_response))

            conn.commit()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'ai_response': ai_response,
            'memory_used': len(memory) > 0,
            'memory_items': len(memory)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


def generate_ai_response(message, memory_context, history):
    """
    Calls AWS Bedrock (Claude 3) passing the user's message, conversation history,
    and agentic memory context as background knowledge.
    """
    import boto3
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    region = os.environ.get('AWS_REGION', 'eu-central-1')

    # Format system prompt with Agentic Memory Context
    system_prompt = (
        "You are Safar AI, a helpful, localized travel assistant for Morocco and Africa.\n"
        "You have access to the user's persistent Agentic Memory preferences listed below.\n"
        "IMPORTANT: You must always respect and tailor your travel/booking recommendations "
        "to match these preferences automatically without reminding the user about them, unless asked.\n\n"
        f"--- USER AGENTIC MEMORY ---\n{memory_context or 'No preferences recorded yet.'}\n"
    )

    # Process history into Claude 3 Message format
    messages = []
    # history contains items ordered from newest to oldest due to LIMIT 10 and DESC.
    # We should reverse it to be chronological!
    for h in reversed(history or []):
        messages.append({
            "role": "user" if h['message_role'] == 'user' else "assistant",
            "content": [{"type": "text", "text": h['message_text']}]
        })

    # Append the new user message
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": message}]
    })

    try:
        # Create boto3 client for Bedrock Runtime
        client = boto3.client('bedrock-runtime', region_name=region)

        # Claude 3 Messages API payload
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.5
        }

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )

        response_body = json.loads(response.get('body').read())
        ai_text = response_body.get('content')[0].get('text')
        return ai_text

    except Exception as e:
        # Fallback helper if Bedrock client fails or environment has no AWS config
        print(f"AWS Bedrock invocation failed ({e}). Falling back to heuristic memory agent.")

        # Heuristic matching
        if 'flight' in message.lower() or 'vol' in message.lower():
            if memory_context:
                return f"I found flights for you! I remember you prefer {memory_context}. Let me search with these preferences."
            return "I'd be happy to help you find flights! What is your destination and budget?"

        if 'hotel' in message.lower():
            return "Searching for hotels based on your preferences..."

        if memory_context:
            return f"Hello! I remember that you prefer {memory_context}. How can I help you today?"

        return "Hello! I'm Safar AI. Tell me about your travel preferences so I can assist you better."


# ============================================================
# 4. BOOKING MANAGEMENT
# ============================================================

@app.route('/api/v1/bookings', methods=['POST'])
def create_booking():
    """Create a new booking"""
    data = request.get_json()

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO bookings 
                    (user_id, booking_type, service_provider, from_location, to_location,
                     departure_date, return_date, amount, currency, pnr_code, booking_details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING booking_id, created_at
            ''', (
                data.get('user_id'), data.get('booking_type'), data.get('service_provider'),
                data.get('from_location'), data.get('to_location'), data.get('departure_date'),
                data.get('return_date'), data.get('amount'), data.get('currency', 'MAD'),
                data.get('pnr_code'), json.dumps(data.get('booking_details', {}))
            ))
            booking = cur.fetchone()
            conn.commit()

        if not booking:
            raise Exception("Failed to create booking.")

        return jsonify({
            'success': True,
            'booking_id': str(booking[0]),
            'created_at': booking[1].isoformat(),
            'status': 'pending'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/v1/bookings/<user_id>', methods=['GET'])
def get_user_bookings(user_id):
    """Get all bookings for a user"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM bookings 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            ''', (user_id,))
            bookings = cur.fetchall()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'bookings': [dict(b) for b in bookings],
            'count': len(bookings)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============================================================
# 5. SERVICES CATALOG
# ============================================================

@app.route('/api/v1/services', methods=['GET'])
def get_services():
    """Get all 36 services of Safar AI"""
    set_number = request.args.get('set', type=int)
    category = request.args.get('category')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if set_number and category:
                cur.execute('''
                    SELECT * FROM services 
                    WHERE set_number = %s AND service_category = %s AND is_active = true
                    ORDER BY screen_number
                ''', (set_number, category))
            elif set_number:
                cur.execute('''
                    SELECT * FROM services 
                    WHERE set_number = %s AND is_active = true
                    ORDER BY screen_number
                ''', (set_number,))
            else:
                cur.execute('''
                    SELECT * FROM services WHERE is_active = true
                    ORDER BY set_number, screen_number
                ''')

            services = cur.fetchall()

        return jsonify({
            'success': True,
            'total_services': len(services),
            'services': [dict(s) for s in services]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============================================================
# 6. AWS LAMBDA HANDLER (for serverless deployment)
# ============================================================

def lambda_handler(event, context):
    """AWS Lambda handler for serverless deployment"""
    from aws_wsgi import response
    return response(app, event, context)


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
