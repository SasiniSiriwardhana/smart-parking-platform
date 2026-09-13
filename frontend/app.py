from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
import os, requests

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'smart-parking-onboarding-secret')

FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8000')

@app.route('/')
def index():
    return redirect(url_for('onboarding_form'))

@app.route('/onboarding', methods=['GET'])
def onboarding_form():
    return render_template('onboarding/form.html')

@app.route('/onboarding/submit', methods=['POST'])
def onboarding_submit():
    payload = {
        'company_name': request.form.get('company_name', '').strip(),
        'contact_person': request.form.get('contact_person', '').strip(),
        'email': request.form.get('email', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'address': request.form.get('address', '').strip(),
    }
    # basic validation
    for field in ['company_name', 'contact_person', 'email']:
        if not payload[field]:
            return render_template('onboarding/_error_partial.html', error=f"{field.replace('_', ' ').title()} is required."), 422
    try:
        resp = requests.post(f"{FASTAPI_URL}/api/clients", json=payload, timeout=10)
        resp.raise_for_status()
        client = resp.json()
        session['client'] = client
        response = make_response('', 200)
        response.headers['HX-Redirect'] = url_for('onboarding_success')
        return response
    except Exception as exc:
        return render_template('onboarding/_error_partial.html', error=str(exc)), 500

@app.route('/onboarding/success', methods=['GET'])
def onboarding_success():
    client = session.pop('client', None)
    if not client:
        return redirect(url_for('onboarding_form'))
    return render_template('onboarding/success.html', client=client)

@app.route('/dashboard')
def dashboard():
    # placeholder demo page
    return render_template('onboarding/dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5000)), debug=True)
