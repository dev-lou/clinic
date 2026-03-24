
from dotenv import load_dotenv
load_dotenv()
import app
c = app.create_app().test_client()

with c.application.test_request_context():
    from flask_login import login_user
    from models import User
    u = User.query.filter_by(role='admin').first()
    if u: login_user(u)
    
    try:
        r = c.post('/analytics/api/predict/health-trends')
        print('Status:', r.status_code)
        print('Data:', r.data.decode('utf-8'))
    except Exception as e:
        print('Error:', e)

