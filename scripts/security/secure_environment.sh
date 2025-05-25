#!/bin/bash

# Script de sécurisation de l'environnement Hadoop et des données

# Configuration des variables
HADOOP_HOME="/usr/local/hadoop"
HADOOP_CONF_DIR="$HADOOP_HOME/etc/hadoop"
SPARK_HOME="/usr/local/spark"
SPARK_CONF_DIR="$SPARK_HOME/conf"

# 1. Configuration de la sécurité Kerberos
echo "Configuration de Kerberos..."

# Installation des packages nécessaires
apt-get update
apt-get install -y krb5-user krb5-config libpam-krb5

# Configuration du fichier krb5.conf
cat > /etc/krb5.conf << EOF
[libdefaults]
    default_realm = HADOOP.LOCAL
    dns_lookup_realm = false
    dns_lookup_kdc = false
    ticket_lifetime = 24h
    forwardable = true
    proxiable = true

[realms]
    HADOOP.LOCAL = {
        kdc = kdc.hadoop.local
        admin_server = kdc.hadoop.local
    }

[domain_realm]
    .hadoop.local = HADOOP.LOCAL
    hadoop.local = HADOOP.LOCAL
EOF

# 2. Configuration de la sécurité HDFS
echo "Configuration de la sécurité HDFS..."

# Activation de la sécurité HDFS
cat > $HADOOP_CONF_DIR/core-site.xml << EOF
<?xml version="1.0"?>
<configuration>
    <property>
        <name>hadoop.security.authentication</name>
        <value>kerberos</value>
    </property>
    <property>
        <name>hadoop.security.authorization</name>
        <value>true</value>
    </property>
    <property>
        <name>hadoop.security.auth_to_local</name>
        <value>DEFAULT</value>
    </property>
</configuration>
EOF

# 3. Configuration des permissions HDFS
echo "Configuration des permissions HDFS..."

# Création des groupes et utilisateurs
groupadd hadoop_users
useradd -g hadoop_users hdfs
useradd -g hadoop_users yarn
useradd -g hadoop_users mapred

# Configuration des permissions HDFS
hdfs dfs -chmod -R 750 /user
hdfs dfs -chown -R hdfs:hadoop_users /user
hdfs dfs -chmod -R 750 /tmp
hdfs dfs -chown -R hdfs:hadoop_users /tmp

# 4. Configuration de la sécurité Spark
echo "Configuration de la sécurité Spark..."

cat > $SPARK_CONF_DIR/spark-defaults.conf << EOF
spark.authenticate true
spark.authenticate.secret your-secret-key
spark.network.sasl.enabled true
spark.ssl.enabled true
spark.ssl.keyStore /path/to/keystore.jks
spark.ssl.keyStorePassword your-keystore-password
spark.ssl.trustStore /path/to/truststore.jks
spark.ssl.trustStorePassword your-truststore-password
EOF

# 5. Configuration du chiffrement des données
echo "Configuration du chiffrement des données..."

# Installation des outils de chiffrement
apt-get install -y openssl

# Configuration du chiffrement HDFS
cat >> $HADOOP_CONF_DIR/hdfs-site.xml << EOF
    <property>
        <name>dfs.encrypt.data.transfer</name>
        <value>true</value>
    </property>
    <property>
        <name>dfs.encrypt.data.transfer.algorithm</name>
        <value>3des</value>
    </property>
    <property>
        <name>dfs.encrypt.data.transfer.cipher.suites</name>
        <value>AES/CTR/NoPadding</value>
    </property>
EOF

# 6. Configuration des pare-feu
echo "Configuration des pare-feu..."

# Configuration d'iptables pour Hadoop
iptables -A INPUT -p tcp --dport 8020 -j ACCEPT  # HDFS NameNode
iptables -A INPUT -p tcp --dport 8030 -j ACCEPT  # YARN ResourceManager
iptables -A INPUT -p tcp --dport 8031 -j ACCEPT  # YARN NodeManager
iptables -A INPUT -p tcp --dport 8032 -j ACCEPT  # YARN ApplicationMaster
iptables -A INPUT -p tcp --dport 8033 -j ACCEPT  # YARN TimelineServer
iptables -A INPUT -p tcp --dport 8088 -j ACCEPT  # YARN Web UI
iptables -A INPUT -p tcp --dport 9000 -j ACCEPT  # HDFS Web UI

# Sauvegarde des règles iptables
iptables-save > /etc/iptables/rules.v4

# 7. Configuration de l'audit
echo "Configuration de l'audit..."

# Installation des outils d'audit
apt-get install -y auditd

# Configuration de l'audit pour Hadoop
cat > /etc/audit/rules.d/hadoop.rules << EOF
-w /usr/local/hadoop -p wa -k hadoop
-w /usr/local/hadoop/etc/hadoop -p wa -k hadoop
-w /var/log/hadoop -p wa -k hadoop
EOF

# Redémarrage du service d'audit
service auditd restart

# 8. Configuration des sauvegardes
echo "Configuration des sauvegardes..."

# Création du script de sauvegarde
cat > /usr/local/bin/backup-hadoop.sh << EOF
#!/bin/bash
BACKUP_DIR="/backup/hadoop"
DATE=\$(date +%Y%m%d)

# Création du répertoire de sauvegarde
mkdir -p \$BACKUP_DIR/\$DATE

# Sauvegarde des configurations
cp -r $HADOOP_CONF_DIR \$BACKUP_DIR/\$DATE/
cp -r $SPARK_CONF_DIR \$BACKUP_DIR/\$DATE/

# Sauvegarde des données HDFS
hdfs dfsadmin -fetchImage \$BACKUP_DIR/\$DATE/fsimage
hdfs dfsadmin -fetchEdits \$BACKUP_DIR/\$DATE/edits

# Compression de la sauvegarde
tar -czf \$BACKUP_DIR/\$DATE.tar.gz \$BACKUP_DIR/\$DATE

# Nettoyage des anciennes sauvegardes (garde les 7 derniers jours)
find \$BACKUP_DIR -type f -mtime +7 -delete
EOF

# Rendre le script exécutable
chmod +x /usr/local/bin/backup-hadoop.sh

# Ajout de la tâche cron pour les sauvegardes quotidiennes
echo "0 2 * * * /usr/local/bin/backup-hadoop.sh" >> /etc/crontab

# 9. Configuration des alertes de sécurité
echo "Configuration des alertes de sécurité..."

# Installation de fail2ban
apt-get install -y fail2ban

# Configuration de fail2ban pour Hadoop
cat > /etc/fail2ban/jail.d/hadoop.conf << EOF
[hadoop-ssh]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

# Redémarrage de fail2ban
service fail2ban restart

echo "=== Configuration de la sécurité terminée ==="
echo "N'oubliez pas de :"
echo "1. Configurer les mots de passe pour les utilisateurs créés"
echo "2. Générer et distribuer les clés Kerberos"
echo "3. Configurer les certificats SSL pour Spark"
echo "4. Tester les sauvegardes"
echo "5. Vérifier les règles de pare-feu" 