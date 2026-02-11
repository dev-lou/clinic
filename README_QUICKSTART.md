# 🚀 Quick Start Guide - ISUFST CareHub Enhanced

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies (for Tailwind CSS)
```bash
npm install
```

### 3. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
# At minimum, set:
# - DATABASE_URL
# - TURSO_AUTH_TOKEN
# - SECRET_KEY
```

### 4. Run Database Migration
```bash
python migrate_database.py
```

### 5. Build Production CSS
```bash
npm run build:css
```

### 6. Create Admin Account
```bash
flask seed-admin
# Default: admin@isufst.edu.ph / admin123
```

### 7. Run the Application
```bash
python app.py
```

The app will be available at: `http://localhost:5000`

---

## 🎯 Testing the New Features

### 1. **Patient Dashboard**
- Login as a student
- Navigate to `/dashboard/`
- View unified health information

### 2. **Symptom Screening**
- Go to `/screening/`
- Select symptoms
- Get AI recommendations

### 3. **Queue Display Board**
- Open `/queue-display/` on a second screen
- TV-friendly view updates in real-time

### 4. **Analytics Dashboard**
- Login as admin/nurse
- Visit `/analytics/`
- View comprehensive metrics

### 5. **REST API**
- Test endpoints at `/api/v1/`
- Use Postman or curl
- Example:
  ```bash
  curl http://localhost:5000/api/v1/appointments \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

### 6. **Search System**
- Login as staff
- Go to `/search/`
- Search across patients, appointments, inventory

---

## 📱 Mobile App Development

The REST API is ready for mobile app integration!

**Base URL:** `http://your-domain/api/v1/`

**Key Endpoints:**
- `POST /auth/login` - Authentication
- `GET /appointments` - List appointments
- `POST /appointments` - Book appointment
- `GET /medical-records` - Health history
- `GET /notifications` - Get notifications

**See:** [ENHANCEMENTS.md](ENHANCEMENTS.md) for full API documentation

---

## 🎨 Customization

### Change Colors
Edit `tailwind.config.js`:
```javascript
colors: {
  'isufst-primary': '#your-color',
  'isufst-secondary': '#your-color',
}
```

Then rebuild:
```bash
npm run build:css
```

### Add New Service Types
Edit `models_extended.py`:
```python
class ServiceType(Enum):
    YOUR_NEW_SERVICE = 'Your New Service'
```

---

## 🐛 Common Issues

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Tailwind CSS not working
```bash
npm install
npm run build:css
```

### Database errors
```bash
python migrate_database.py
```

### Email not sending
- Check `.env` MAIL_* settings
- For Gmail, enable "App Passwords"

---

## 📚 Documentation

- **Full Features:** See [ENHANCEMENTS.md](ENHANCEMENTS.md)
- **API Reference:** See API section in ENHANCEMENTS.md
- **Database Schema:** See `models.py` and `models_extended.py`

---

## 🎓 For Capstone Defense

### Talking Points:
1. **Integration** - Show how queue → appointments → visits → prescriptions all connect
2. **Innovation** - Demo AI symptom screening and real-time queue display
3. **Scalability** - Explain REST API for future mobile app
4. **Security** - Discuss RBAC and audit logging
5. **Professionalism** - Point out production Tailwind, error handling, notifications

### Demo Flow:
1. Student checks symptoms → Books appointment
2. Admin views in analytics dashboard
3. Show real-time queue on TV display
4. Process visit → Write prescription
5. Show health timeline with all connected data

**Good luck! 🚀**
