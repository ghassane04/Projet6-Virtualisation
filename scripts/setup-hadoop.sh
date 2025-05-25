#!/bin/bash

# Configuration de l'environnement Hadoop
echo "=== Configuration de l'environnement Hadoop ==="

# Installation des dépendances
sudo apt-get update
sudo apt-get install -y openjdk-8-jdk python3-pip

# Configuration de Java
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" >> ~/.bashrc

# Installation de Hadoop
wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /usr/local/hadoop
echo "export HADOOP_HOME=/usr/local/hadoop" >> ~/.bashrc
echo "export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin" >> ~/.bashrc

# Configuration de Hadoop
cat > $HADOOP_HOME/etc/hadoop/core-site.xml << EOF
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>fs.gs.impl</name>
        <value>com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem</value>
    </property>
    <property>
        <name>fs.AbstractFileSystem.gs.impl</name>
        <value>com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS</value>
    </property>
</configuration>
EOF

cat > $HADOOP_HOME/etc/hadoop/hdfs-site.xml << EOF
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/usr/local/hadoop/data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/usr/local/hadoop/data/datanode</value>
    </property>
</configuration>
EOF

# Installation de PySpark
pip3 install pyspark==3.3.0
pip3 install google-cloud-storage

# Configuration des permissions
sudo chown -R $USER:$USER $HADOOP_HOME
mkdir -p $HADOOP_HOME/data/namenode
mkdir -p $HADOOP_HOME/data/datanode

# Formatage du système de fichiers HDFS
hdfs namenode -format

# Démarrage des services Hadoop
start-dfs.sh
start-yarn.sh

echo "=== Configuration Hadoop terminée ==="
echo "Vérification des services Hadoop :"
jps

# Configuration de l'accès à Google Cloud Storage
echo "=== Configuration de l'accès à Google Cloud Storage ==="
gcloud auth application-default login

echo "=== Installation terminée ===" 