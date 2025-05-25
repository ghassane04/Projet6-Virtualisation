# Projet Big Data Analytique avec Google Cloud et Apache Hadoop

Ce projet met en place une solution de Big Data analytique pour une entreprise de marketing, utilisant Google Cloud Platform et Apache Hadoop.

## Structure du Projet

```
.
├── README.md
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── scripts/
│   ├── setup-hadoop.sh
│   └── data-processing/
│       ├── process_data.py
│       └── analyze_data.py
└── data/
    └── sample_data.csv
```

## Prérequis

- Compte Google Cloud Platform
- Google Cloud SDK installé
- Terraform installé
- Python 3.7+
- Apache Hadoop

## Configuration

1. Initialiser Terraform :
```bash
cd terraform
terraform init
```

2. Configurer les variables dans `terraform/variables.tf`

3. Déployer l'infrastructure :
```bash
terraform apply
```

4. Exécuter le script de configuration Hadoop :
```bash
./scripts/setup-hadoop.sh
```

## Utilisation

1. Traitement des données :
```bash
python scripts/data-processing/process_data.py
```

2. Analyse des données :
```bash
python scripts/data-processing/analyze_data.py
```

## Architecture

- Google Compute Engine : Machines virtuelles pour le cluster Hadoop
- Google Cloud Storage : Stockage des données
- Apache Hadoop : Traitement distribué des données
- Python : Scripts de traitement et d'analyse 

## Sécurité

### Mesures de sécurité mises en place

1. **Réseau et Pare-feu**
   - VPC dédié pour le cluster Hadoop
   - Règles de pare-feu restrictives
   - Isolation réseau des composants

2. **IAM et Authentification**
   - Service account dédié pour Hadoop
   - Permissions minimales requises
   - Gestion des accès basée sur les rôles

3. **Chiffrement des données**
   - Chiffrement au repos avec Cloud KMS
   - Rotation automatique des clés (90 jours)
   - Chiffrement en transit (TLS)

4. **Sauvegardes**
   - Sauvegardes quotidiennes automatiques
   - Versioning des données
   - Rétention configurable (90 jours par défaut)

### Vérification de la sécurité

Pour exécuter les vérifications de sécurité :

```bash
chmod +x scripts/security-check.sh
./scripts/security-check.sh
```

Le script vérifie :
- Les règles de pare-feu
- Les permissions IAM
- L'état du chiffrement
- Les sauvegardes
- Les logs de sécurité
- Les mises à jour système 