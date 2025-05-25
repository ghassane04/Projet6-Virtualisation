# Configuration de Cloud KMS pour le chiffrement
resource "google_kms_key_ring" "hadoop_keyring" {
  name     = "hadoop-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "hadoop_key" {
  name     = "hadoop-key"
  key_ring = google_kms_key_ring.hadoop_keyring.id

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  rotation_period = "7776000s" # 90 jours
}

# Configuration de Cloud Storage pour les sauvegardes
resource "google_storage_bucket" "hadoop_backups" {
  name          = "${var.project_id}-hadoop-backups"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90 # 90 jours
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.hadoop_key.id
  }
}

# Politique de sauvegarde automatique
resource "google_storage_transfer_job" "hadoop_backup_job" {
  name        = "hadoop-daily-backup"
  description = "Sauvegarde quotidienne des données Hadoop"
  project     = var.project_id

  schedule {
    schedule_start_date {
      year  = 2024
      month = 1
      day   = 1
    }
    schedule_end_date {
      year  = 2025
      month = 12
      day   = 31
    }
    start_time_of_day {
      hours   = 2
      minutes = 0
      seconds = 0
      nanos   = 0
    }
    repeat_interval = "86400s" # 24 heures
  }

  transfer_spec {
    object_conditions {
      include_prefixes = ["data/"]
    }
    transfer_options {
      delete_objects_unique_in_sink = false
    }
    gcs_data_sink {
      bucket_name = google_storage_bucket.hadoop_backups.name
    }
  }
} 