# Cloud Run Services

# Backend API Service
resource "google_cloud_run_v2_service" "backend" {
  name     = "benimmasalim-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    # Limit concurrent requests per instance so heavy AI jobs don't
    # overwhelm a single container.  Cloud Run will spin up more
    # instances instead.
    max_instance_request_concurrency = var.environment == "prod" ? 20 : 40

    scaling {
      min_instance_count = var.environment == "prod" ? 2 : 0
      max_instance_count = var.environment == "prod" ? 15 : 2
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benimmasalim/benimmasalim-backend:latest"

      resources {
        limits = {
          cpu    = var.environment == "prod" ? "2" : "1"
          memory = var.environment == "prod" ? "4Gi" : "512Mi"
        }
        # Keep CPU always allocated in prod so scale-up is instant
        cpu_idle = var.environment == "prod" ? false : true
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = "JWT_SECRET_KEY"
            version = "latest"
          }
        }
      }

      env {
        name  = "GCS_BUCKET_RAW"
        value = google_storage_bucket.raw_uploads.name
      }

      env {
        name  = "GCS_BUCKET_GENERATED"
        value = google_storage_bucket.generated_books.name
      }

      # Cloud SQL connection
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        timeout_seconds       = 5
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        period_seconds    = 30
        timeout_seconds   = 5
        failure_threshold = 3
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    service_account = google_service_account.backend.email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.apis,
    google_sql_database_instance.main
  ]
}

# Frontend Service
resource "google_cloud_run_v2_service" "frontend" {
  name     = "benimmasalim-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 5 : 2
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benimmasalim/benimmasalim-frontend:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = var.environment == "prod" ? "1Gi" : "512Mi"
        }
        cpu_idle = true
      }

      ports {
        container_port = 3000
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = "https://api.benimmasalim.com"
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.apis]
}

# Service Account for Backend
resource "google_service_account" "backend" {
  account_id   = "benimmasalim-backend"
  display_name = "Benim Masalım Backend Service Account"
}

# IAM: Backend can access Cloud SQL
resource "google_project_iam_member" "backend_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# IAM: Backend can access GCS
resource "google_project_iam_member" "backend_storage" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# IAM: Backend can access Secret Manager
resource "google_project_iam_member" "backend_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# IAM: Backend can enqueue Cloud Tasks
resource "google_project_iam_member" "backend_tasks" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Allow public access
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}
