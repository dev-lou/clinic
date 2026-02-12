# Database Configuration Guide

## The Turso + Render Issue

**Problem**: Turso's `sqlalchemy-libsql` package requires Rust compilation, which causes worker timeouts and crashes on Render's free tier.

**Error symptoms**:
- 502 Bad Gateway
- Worker timeouts
- "Resource deadlock avoided" errors  
- Workers being killed by SIGKILL

## Solutions

### Option 1: SQLite (Current - Works Immediately) ✅

**Best for**: Development, testing, small deployments

The app is now configured to use local SQLite by default. This works on both local and Render without any setup:

- **Local**: `instance/carehub_dev.db`
- **Render**: `instance/carehub_dev.db` (stored on Render's disk)

**Pros**:
- No configuration needed
- Works immediately
- No Rust compilation
- Fast for development

**Cons**:
- Data may be lost on Render redeployments (free tier)
- Not suitable for high-traffic production

### Option 2: PostgreSQL (Recommended for Render Production) 🐘

**Best for**: Production deployments on Render

1. **On Render Dashboard**:
   - Go to your service
   - Click "New +" → "PostgreSQL"
   - Select Free plan
   - Create database

2. **Render will automatically set** `DATABASE_URL` environment variable

3. **Deploy** - it will work automatically! 

**Pros**:
- Free tier available
- Data persists across deployments
- Production-ready
- No Rust required

**Cons**:
- Slightly more complex than SQLite

### Option 3: Turso (For Advanced Users) 🚀

**Best for**: Those who specifically need Turso's features

To use Turso, you need a server with Rust installed:

1. **Local Development with Turso**:
   ```bash
   # Install Rust first
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Then install Python package
   pip install sqlalchemy-libsql
   
   # Add to .env
   DATABASE_URL=libsql://your-db.turso.io
   TURSO_AUTH_TOKEN=your_token_here
   ```

2. **For Render**: Not recommended due to Rust compilation issues on free tier.

## Current Configuration

The app is configured to:
- ✅ Use **SQLite** by default (no DATABASE_URL needed)
- ✅ Support **PostgreSQL** if DATABASE_URL is set to `postgresql://...`
- ⚠️ Turso requires manual Rust installation

## Quick Start

### Local Development
```bash
# No configuration needed!
python app.py
```

### Deploy to Render

1. **Push code**:
   ```bash
   git add .
   git commit -m "Fix Render deployment"
   git push origin main
   ```

2. **Done!** App will use SQLite automatically.

3. **(Optional) Add PostgreSQL**:
   - Create PostgreSQL database on Render
   - Render auto-sets DATABASE_URL
   - Redeploy

## Environment Variables

### Required (Both Local & Render):
```env
SECRET_KEY=your-secret-key
```

### Optional:
```env
DATABASE_URL=postgresql://...  # If using PostgreSQL
GEMINI_API_KEY=your_api_key    # For AI features
```

### Not needed anymore:
```env
TURSO_AUTH_TOKEN  # Removed to avoid Rust compilation
```

## Summary

✅ **Just deployed?** Your app should work with SQLite immediately.

📝 **Want persistence?** Add PostgreSQL from Render dashboard.

🚀 **Want Turso?** Install Rust locally, not recommended for Render free tier.
