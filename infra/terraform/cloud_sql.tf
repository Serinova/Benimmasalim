# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "main" {
  name             = "benimmasalim-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.environment == "prod" ? "db-custom-2-4096" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = var.environment == "prod" ? 50 : 10
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled = true
      # For Cloud Run connection
      authorized_networks {
        name  = "allow-all"
        value = "0.0.0.0/0"
      }
    }

    database_flags {
      name  = "max_connections"
      value = var.environment == "prod" ? "200" : "50"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = var.environment == "prod"

  depends_on = [google_project_service.apis]
}

# Database
resource "google_sql_database" "main" {
  name     = "benimmasalim"
  instance = google_sql_database_instance.main.name
}

# Database User
resource "google_sql_user" "app" {
  name     = "benimmasalim_app"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

# Store password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password-${var.environment}"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Database URL secret
resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+asyncpg://${google_sql_user.app.name}:${random_password.db_password.result}@/${google_sql_database.main.name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
}

output "db_connection_name" {
  value = google_sql_database_instance.main.connection_name
}
