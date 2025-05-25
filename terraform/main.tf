provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# VPC Network
resource "google_compute_network" "hadoop_network" {
  name                    = "hadoop-network"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "hadoop_subnet" {
  name          = "hadoop-subnet"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.hadoop_network.id
  region        = var.region
}

# Firewall rules
resource "google_compute_firewall" "hadoop_firewall" {
  name    = "hadoop-firewall"
  network = google_compute_network.hadoop_network.name

  allow {
    protocol = "tcp"
    ports    = ["22", "8088", "9870", "9000"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# Configuration du bucket Cloud Storage pour les données
resource "google_storage_bucket" "hadoop_data" {
  name          = "${var.project_id}-hadoop-data"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# Configuration des instances Compute Engine pour le cluster Hadoop
resource "google_compute_instance" "hadoop_master" {
  name         = "hadoop-master"
  machine_type = "e2-standard-4"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 100
    }
  }

  network_interface {
    network = google_compute_network.hadoop_network.name
    subnetwork = google_compute_subnetwork.hadoop_subnet.name
    access_config {
      // Éphemère IP publique
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_pub_key_path)}"
  }

  tags = ["hadoop-node", "hadoop-master"]
}

resource "google_compute_instance" "hadoop_workers" {
  count        = var.worker_count
  name         = "hadoop-worker-${count.index + 1}"
  machine_type = "e2-standard-2"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 100
    }
  }

  network_interface {
    network = google_compute_network.hadoop_network.name
    subnetwork = google_compute_subnetwork.hadoop_subnet.name
    access_config {
      // Éphemère IP publique
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_pub_key_path)}"
  }

  tags = ["hadoop-node", "hadoop-worker"]
}

# Configuration du service account pour Hadoop
resource "google_service_account" "hadoop_service_account" {
  account_id   = "hadoop-service-account"
  display_name = "Hadoop Service Account"
}

# Attribution des rôles au service account
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

# Configuration des variables d'environnement pour les instances
resource "google_compute_instance_template" "hadoop_template" {
  name_prefix  = "hadoop-template-"
  machine_type = "e2-standard-2"

  disk {
    source_image = "debian-cloud/debian-11"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network = google_compute_network.hadoop_network.name
    subnetwork = google_compute_subnetwork.hadoop_subnet.name
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_pub_key_path)}"
  }

  service_account {
    email  = google_service_account.hadoop_service_account.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    create_before_destroy = true
  }
} 