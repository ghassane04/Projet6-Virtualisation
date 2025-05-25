#!/bin/bash

# Script de vérification de sécurité pour le cluster Hadoop

echo "=== Vérification de la sécurité du cluster Hadoop ==="

# Vérification des règles de pare-feu
echo "Vérification des règles de pare-feu..."
gcloud compute firewall-rules list --filter="network=hadoop-network" --format="table(name,network,direction,priority,sourceRanges.list(),allowed[].map().firewall_rule().list(),targetTags.list())"

# Vérification des IAM
echo "Vérification des permissions IAM..."
gcloud projects get-iam-policy $PROJECT_ID --format="table(bindings.role,bindings.members)"

# Vérification du chiffrement
echo "Vérification du chiffrement KMS..."
gcloud kms keys list --keyring=hadoop-keyring --location=$REGION --format="table(name,primary.name,primary.state)"

# Vérification des sauvegardes
echo "Vérification des sauvegardes..."
gsutil ls -L gs://$PROJECT_ID-hadoop-backups

# Vérification des logs de sécurité
echo "Vérification des logs de sécurité..."
gcloud logging read "resource.type=gce_instance AND severity>=WARNING" --limit=10 --format="table(timestamp,severity,textPayload)"

# Vérification des mises à jour système
echo "Vérification des mises à jour système..."
gcloud compute instances list --format="table(name,status,lastStartTimestamp)"

echo "=== Fin de la vérification de sécurité ===" 