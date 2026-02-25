#!/usr/bin/env python3
"""Test GCS connection and upload."""

import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

def test_gcs():
    """Test GCS connection."""
    from google.cloud import storage
    from google.oauth2 import service_account

    # Get credentials
    creds_json = os.environ.get('GCS_CREDENTIALS_JSON')
    if not creds_json:
        # Try loading from file
        creds_file = os.path.join(os.path.dirname(__file__), '..', 'gcs-credentials.json')
        if os.path.exists(creds_file):
            with open(creds_file) as f:
                creds_json = f.read()
        else:
            print("[X] GCS credentials bulunamadi")
            return False

    try:
        creds_info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        project_id = creds_info.get('project_id', 'gen-lang-client-0784096400')

        print(f"Project ID: {project_id}")
        print(f"Service Account: {creds_info.get('client_email')}")

        client = storage.Client(project=project_id, credentials=credentials)

        bucket_name = os.environ.get('GCS_BUCKET_IMAGES', 'benimmasalim-images')
        print(f"\nBucket: {bucket_name}")

        bucket = client.bucket(bucket_name)

        if bucket.exists():
            print(f"[OK] Bucket '{bucket_name}' mevcut")
        else:
            print(f"Bucket '{bucket_name}' olusturuluyor...")
            bucket = client.create_bucket(bucket_name, location='europe-west1')
            bucket.make_public(recursive=True, future=True)
            print("[OK] Bucket olusturuldu")

        # Test upload
        print("\nTest dosyasi yukleniyor...")
        blob = bucket.blob('test/hello.txt')
        blob.upload_from_string('Hello from BenimMasalim! ' + str(os.urandom(4).hex()))
        blob.make_public()
        print("[OK] Test dosyasi yuklendi")
        print(f"  URL: {blob.public_url}")

        # Test image upload
        print("\nTest gorseli yukleniyor...")
        import base64
        # Simple 1x1 red PNG
        red_pixel = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        blob = bucket.blob('test/test_image.png')
        blob.upload_from_string(red_pixel, content_type='image/png')
        blob.make_public()
        print("[OK] Test gorseli yuklendi")
        print(f"  URL: {blob.public_url}")

        return True

    except Exception as e:
        print(f"[X] Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("GCS Bağlantı Testi")
    print("="*50)
    success = test_gcs()
    print("\n" + "="*50)
    print("SONUC:", "BASARILI" if success else "BASARISIZ")
    print("="*50)
