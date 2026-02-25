# Cloud Storage Buckets

# Raw uploads bucket (child photos - KVKK 30 day retention)
resource "google_storage_bucket" "raw_uploads" {
  name     = "${var.project_id}-raw-uploads"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30  # KVKK compliance - auto delete after 30 days
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = false
  }

  # Encryption at rest
  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  cors {
    origin          = ["https://benimmasalim.com", "http://localhost:3000"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["Content-Type", "Content-Length"]
    max_age_seconds = 3600
  }

  depends_on = [google_kms_crypto_key_iam_binding.storage_key]
}

# Generated books bucket
resource "google_storage_bucket" "generated_books" {
  name     = "${var.project_id}-generated-books"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = ["https://benimmasalim.com", "http://localhost:3000"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Content-Length"]
    max_age_seconds = 86400
  }
}

# Audio files bucket
resource "google_storage_bucket" "audio_files" {
  name     = "${var.project_id}-audio-files"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  cors {
    origin          = ["https://benimmasalim.com", "http://localhost:3000"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Content-Length", "Accept-Ranges"]
    max_age_seconds = 86400
  }
}

# Static assets bucket (overlays, thumbnails)
resource "google_storage_bucket" "static_assets" {
  name     = "${var.project_id}-static-assets"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  # Enable CDN
  website {
    main_page_suffix = "index.html"
  }
}

# KMS Key for encryption
resource "google_kms_key_ring" "storage" {
  name     = "storage-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "storage_key" {
  name     = "storage-encryption-key"
  key_ring = google_kms_key_ring.storage.id

  rotation_period = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

# Grant Cloud Storage service account access to KMS key
resource "google_kms_crypto_key_iam_binding" "storage_key" {
  crypto_key_id = google_kms_crypto_key.storage_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"

  members = [
    "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com",
  ]
}

data "google_project" "project" {}

output "bucket_raw_uploads" {
  value = google_storage_bucket.raw_uploads.name
}

output "bucket_generated_books" {
  value = google_storage_bucket.generated_books.name
}

output "bucket_audio_files" {
  value = google_storage_bucket.audio_files.name
}
