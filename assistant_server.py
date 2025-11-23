from flask import Flask, request, jsonify
from flask_cors import CORS
import personal_assistant as pa
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Ensure the agent is created on startup (lazy creation is fine too)
agent = pa.get_agent()

# File to store contact form submissions
CONTACT_SUBMISSIONS_FILE = 'contact_submissions.json'


def load_submissions():
    """Load existing submissions from file."""
    if os.path.exists(CONTACT_SUBMISSIONS_FILE):
        try:
            with open(CONTACT_SUBMISSIONS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_submissions(submissions):
    """Save submissions to file."""
    try:
        with open(CONTACT_SUBMISSIONS_FILE, 'w') as f:
            json.dump(submissions, f, indent=2)
    except Exception as e:
        print(f"Error saving submissions: {e}")


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'no message provided'}), 400
    try:
        reply = pa.respond_to_query(message)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': 'assistant error', 'details': str(e)}), 500


@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submissions."""
    try:
        data = request.get_json(force=True)
        
        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        reason = data.get('reason', '').strip()
        
        if not name or not email or not reason:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create submission record
        submission = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'email': email,
            'phone': data.get('phone', '').strip(),
            'reason': reason,
            'message': data.get('message', '').strip()
        }
        
        # Load, append, and save
        submissions = load_submissions()
        submissions.append(submission)
        save_submissions(submissions)
        
        print(f"✓ Contact form submission from {name} ({email})")
        return jsonify({'success': True, 'message': 'Thank you! Your message has been received.'}), 200
    except Exception as e:
        print(f"✗ Contact form error: {e}")
        return jsonify({'error': 'Failed to process submission', 'details': str(e)}), 500


if __name__ == '__main__':
    # Run on port 7860 by default; adjust if needed
    app.run(host='0.0.0.0', port=7860)
