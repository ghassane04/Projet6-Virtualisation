#!/bin/bash

# Configuration du pipeline de traitement de données

# Création des répertoires HDFS
hdfs dfs -mkdir -p /user/data/raw
hdfs dfs -mkdir -p /user/data/processed
hdfs dfs -mkdir -p /user/data/analysis

# Installation des dépendances Python supplémentaires
pip3 install pandas numpy scikit-learn matplotlib seaborn

# Configuration des variables d'environnement pour PySpark
echo "export PYSPARK_PYTHON=python3" >> ~/.bashrc
echo "export PYSPARK_DRIVER_PYTHON=python3" >> ~/.bashrc
echo "export SPARK_HOME=/usr/local/spark" >> ~/.bashrc
echo "export PATH=$PATH:$SPARK_HOME/bin" >> ~/.bashrc

# Installation de Spark
wget https://dlcdn.apache.org/spark/spark-3.3.0/spark-3.3.0-bin-hadoop3.tgz
tar -xzf spark-3.3.0-bin-hadoop3.tgz
sudo mv spark-3.3.0-bin-hadoop3 /usr/local/spark

# Configuration de Spark
cat > /usr/local/spark/conf/spark-defaults.conf << EOF
spark.master                     yarn
spark.driver.memory              4g
spark.executor.memory            2g
spark.executor.cores             2
spark.dynamicAllocation.enabled  true
spark.shuffle.service.enabled    true
EOF

# Copie des données d'exemple vers HDFS
hdfs dfs -put /path/to/sample_data.csv /user/data/raw/

echo "=== Configuration du pipeline terminée ===" 