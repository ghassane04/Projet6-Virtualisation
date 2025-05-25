# Service account pour le cluster Hadoop
resource "google_service_account" "hadoop_service_account" {
  account_id   = "hadoop-service-account"
  display_name = "Hadoop Service Account"
}

# Rôles IAM pour le service account
resource "google_project_iam_member" "hadoop_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.hadoop_service_account.email}"
}

resource "google_project_iam_member" "hadoop_compute_admin" {
  project = var.project_id
  role    = "roles/compute.admin"
  member  = "serviceAccount:${google_service_account.hadoop_service_account.email}"
}

resource "google_project_iam_member" "hadoop_logging_admin" {
  project = var.project_id
  role    = "roles/logging.admin"
  member  = "serviceAccount:${google_service_account.hadoop_service_account.email}"
}

# Rôle pour l'accès aux données chiffrées
resource "google_project_iam_member" "hadoop_kms_admin" {
  project = var.project_id
  role    = "roles/cloudkms.admin"
  member  = "serviceAccount:${google_service_account.hadoop_service_account.email}"
} 