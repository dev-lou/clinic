"""
Supabase Storage utility for profile image uploads.
Uses the Supabase REST API with apikey header auth.
"""
import os
import uuid
import requests
from urllib.parse import quote as url_quote
from werkzeug.utils import secure_filename

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SECRET_KEY = os.environ.get('SUPABASE_SECRET_KEY', '')
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'Profile Images')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _bucket_path(path=''):
    """URL-encode bucket name for use in REST API paths."""
    encoded_bucket = url_quote(SUPABASE_BUCKET, safe='')
    if path:
        return f"{encoded_bucket}/{path}"
    return encoded_bucket


def upload_profile_image(file, user_id):
    """
    Upload a profile image to Supabase Storage via REST API.
    Returns the public URL on success, or None on failure.
    """
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        raise ValueError('File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP.')

    # Read file and check size
    file_data = file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise ValueError('File too large. Maximum size is 5 MB.')

    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"user_{user_id}/{uuid.uuid4().hex}.{ext}"

    # Determine content type
    content_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
    }
    content_type = content_types.get(ext, 'image/jpeg')

    # Upload via Supabase Storage REST API
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{_bucket_path(filename)}"
    headers = {
        'apikey': SUPABASE_SECRET_KEY,
        'Content-Type': content_type,
        'x-upsert': 'true',
    }

    try:
        resp = requests.post(upload_url, headers=headers, data=file_data, timeout=30)

        if resp.status_code in (200, 201):
            # Return public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{_bucket_path(filename)}"
            return public_url
        else:
            print(f"Supabase upload failed: {resp.status_code} — {resp.text}")
            raise ValueError(f'Upload failed (status {resp.status_code}). Please try again.')
    except requests.RequestException as e:
        print(f"Supabase upload error: {e}")
        raise ValueError('Could not connect to storage service. Please try again later.')


def delete_profile_image(image_url):
    """Delete an old profile image from Supabase Storage."""
    if not image_url or SUPABASE_BUCKET not in image_url and url_quote(SUPABASE_BUCKET, safe='') not in image_url:
        return

    # Extract path after /public/{bucket}/
    try:
        # Try both encoded and unencoded bucket name
        encoded = url_quote(SUPABASE_BUCKET, safe='')
        if f"/public/{encoded}/" in image_url:
            path = image_url.split(f"/public/{encoded}/")[1]
        elif f"/public/{SUPABASE_BUCKET}/" in image_url:
            path = image_url.split(f"/public/{SUPABASE_BUCKET}/")[1]
        else:
            return
    except (IndexError, AttributeError):
        return

    delete_url = f"{SUPABASE_URL}/storage/v1/object/{_bucket_path()}"
    headers = {
        'apikey': SUPABASE_SECRET_KEY,
        'Content-Type': 'application/json',
    }

    try:
        requests.delete(delete_url, headers=headers, json={'prefixes': [path]}, timeout=15)
    except requests.RequestException:
        pass  # Non-critical — old file stays but won't be referenced
