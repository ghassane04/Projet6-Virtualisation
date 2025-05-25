resource "google_compute_network" "hadoop_network" {
  name                    = "hadoop-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "hadoop_subnet" {
  name          = "hadoop-subnet"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.hadoop_network.id
  region        = var.region
}

# Règles de pare-feu pour le cluster Hadoop
resource "google_compute_firewall" "hadoop_internal" {
  name    = "hadoop-internal"
  network = google_compute_network.hadoop_network.name

  allow {
    protocol = "tcp"
    ports    = ["8020", "9000", "50070", "50075", "50010", "50020", "50090"]
  }

  source_ranges = ["10.0.0.0/24"]
  target_tags   = ["hadoop-node"]
}

resource "google_compute_firewall" "hadoop_ssh" {
  name    = "hadoop-ssh"
  network = google_compute_network.hadoop_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hadoop-node"]
}

# Règle pour bloquer tout le trafic par défaut
resource "google_compute_firewall" "default_deny" {
  name    = "default-deny"
  network = google_compute_network.hadoop_network.name

  deny {
    protocol = "tcp"
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hadoop-node"]
} 