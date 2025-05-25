from google.cloud import storage
from google.cloud import kms
import os
import json
import logging
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StorageSecurityManager:
    def __init__(self, project_id, bucket_name):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.kms_client = kms.KeyManagementServiceClient()
        
    def configure_bucket_security(self):
        """Configure la sécurité du bucket GCS"""
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
            
            # 1. Configuration du chiffrement par défaut
            bucket.encryption = {
                'defaultKmsKeyName': f'projects/{self.project_id}/locations/global/keyRings/hadoop-keyring/cryptoKeys/hadoop-key'
            }
            
            # 2. Configuration des IAM
            policy = bucket.get_iam_policy()
            
            # Ajout des rôles nécessaires
            policy.bindings.append({
                'role': 'roles/storage.objectViewer',
                'members': ['group:hadoop-users@your-domain.com']
            })
            
            policy.bindings.append({
                'role': 'roles/storage.objectCreator',
                'members': ['serviceAccount:hadoop-service@your-project.iam.gserviceaccount.com']
            })
            
            bucket.set_iam_policy(policy)
            
            # 3. Configuration des règles de rétention
            bucket.retention_policy = {
                'retentionPeriod': 90 * 24 * 60 * 60  # 90 jours en secondes
            }
            
            # 4. Activation de la versioning
            bucket.versioning_enabled = True
            
            # 5. Configuration des logs d'audit
            bucket.enable_logging(
                destination_bucket=f'gs://{self.bucket_name}-logs',
                log_object_prefix='audit-logs'
            )
            
            bucket.update()
            logger.info(f"Configuration de sécurité terminée pour le bucket {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de la sécurité: {str(e)}")
            raise
    
    def setup_kms_key(self):
        """Configure une clé KMS pour le chiffrement"""
        try:
            # Création du keyring
            keyring_id = 'hadoop-keyring'
            keyring_path = self.kms_client.key_ring_path(
                self.project_id, 'global', keyring_id
            )
            
            try:
                self.kms_client.get_key_ring(name=keyring_path)
            except Exception:
                parent = f'projects/{self.project_id}/locations/global'
                self.kms_client.create_key_ring(
                    request={
                        'parent': parent,
                        'key_ring_id': keyring_id,
                        'key_ring': {}
                    }
                )
            
            # Création de la clé
            key_id = 'hadoop-key'
            key_path = self.kms_client.crypto_key_path(
                self.project_id, 'global', keyring_id, key_id
            )
            
            try:
                self.kms_client.get_crypto_key(name=key_path)
            except Exception:
                self.kms_client.create_crypto_key(
                    request={
                        'parent': keyring_path,
                        'crypto_key_id': key_id,
                        'crypto_key': {
                            'purpose': 'ENCRYPT_DECRYPT',
                            'version_template': {
                                'algorithm': 'GOOGLE_SYMMETRIC_ENCRYPTION',
                                'protection_level': 'SOFTWARE'
                            },
                            'rotation_period': {'seconds': 90 * 24 * 60 * 60}  # 90 jours
                        }
                    }
                )
            
            logger.info("Configuration KMS terminée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration KMS: {str(e)}")
            raise
    
    def setup_lifecycle_rules(self):
        """Configure les règles de cycle de vie des objets"""
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
            
            lifecycle_rules = {
                'lifecycle': {
                    'rule': [
                        {
                            'action': {
                                'type': 'Delete'
                            },
                            'condition': {
                                'age': 365,  # Suppression après 1 an
                                'isLive': True
                            }
                        },
                        {
                            'action': {
                                'type': 'Delete'
                            },
                            'condition': {
                                'numNewerVersions': 3,  # Garde les 3 dernières versions
                                'isLive': False
                            }
                        }
                    ]
                }
            }
            
            bucket.lifecycle_rules = lifecycle_rules
            bucket.update()
            
            logger.info("Règles de cycle de vie configurées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des règles de cycle de vie: {str(e)}")
            raise
    
    def setup_audit_logging(self):
        """Configure la journalisation d'audit"""
        try:
            # Création du bucket pour les logs
            log_bucket_name = f'{self.bucket_name}-logs'
            log_bucket = self.storage_client.create_bucket(
                log_bucket_name,
                location='EUROPE-WEST1',
                storage_class='STANDARD'
            )
            
            # Configuration des IAM pour les logs
            policy = log_bucket.get_iam_policy()
            policy.bindings.append({
                'role': 'roles/storage.objectViewer',
                'members': ['group:audit-team@your-domain.com']
            })
            log_bucket.set_iam_policy(policy)
            
            logger.info("Journalisation d'audit configurée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de la journalisation: {str(e)}")
            raise

def main():
    # Configuration
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    bucket_name = f'{project_id}-hadoop-data'
    
    try:
        # Initialisation du gestionnaire de sécurité
        security_manager = StorageSecurityManager(project_id, bucket_name)
        
        # Configuration de la sécurité
        logger.info("Démarrage de la configuration de sécurité...")
        
        # 1. Configuration KMS
        security_manager.setup_kms_key()
        
        # 2. Configuration du bucket
        security_manager.configure_bucket_security()
        
        # 3. Configuration des règles de cycle de vie
        security_manager.setup_lifecycle_rules()
        
        # 4. Configuration de l'audit
        security_manager.setup_audit_logging()
        
        logger.info("Configuration de sécurité terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de sécurité: {str(e)}")
        raise

if __name__ == "__main__":
    main() 