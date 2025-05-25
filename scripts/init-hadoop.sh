#!/bin/bash

# Variables
HADOOP_VERSION="3.3.6"
JAVA_VERSION="8"
HADOOP_HOME="/usr/local/hadoop"
HADOOP_CONF_DIR="$HADOOP_HOME/etc/hadoop"

# Installation des dépendances
sudo apt-get update
sudo apt-get install -y openjdk-${JAVA_VERSION}-jdk python3-pip wget

# Configuration de Java
export JAVA_HOME=/usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-${JAVA_VERSION}-openjdk-amd64" >> ~/.bashrc

# Installation de Hadoop
wget https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz
tar -xzf hadoop-${HADOOP_VERSION}.tar.gz
sudo mv hadoop-${HADOOP_VERSION} ${HADOOP_HOME}

# Configuration des variables d'environnement
echo "export HADOOP_HOME=${HADOOP_HOME}" >> ~/.bashrc
echo "export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin" >> ~/.bashrc
source ~/.bashrc

# Configuration de Hadoop
cat > ${HADOOP_CONF_DIR}/core-site.xml << EOF
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://hadoop-master:9000</value>
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

cat > ${HADOOP_CONF_DIR}/hdfs-site.xml << EOF
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>3</value>
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

cat > ${HADOOP_CONF_DIR}/mapred-site.xml << EOF
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.jobhistory.address</name>
        <value>hadoop-master:10020</value>
    </property>
</configuration>
EOF

cat > ${HADOOP_CONF_DIR}/yarn-site.xml << EOF
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>hadoop-master</value>
    </property>
</configuration>
EOF

# Configuration des workers
if [ "$(hostname)" = "hadoop-master" ]; then
    echo "hadoop-master" > ${HADOOP_CONF_DIR}/workers
    for i in $(seq 1 3); do
        echo "hadoop-worker-$i" >> ${HADOOP_CONF_DIR}/workers
    done
    
    # Formatage du système de fichiers HDFS
    hdfs namenode -format
    
    # Démarrage des services
    start-dfs.sh
    start-yarn.sh
    mapred --daemon start historyserver
fi

# Installation de PySpark
pip3 install pyspark==3.3.0
pip3 install google-cloud-storage

echo "=== Configuration Hadoop terminée sur $(hostname) ===" 