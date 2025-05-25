from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
import os

def create_spark_session():
    """Crée une session Spark avec la configuration appropriée"""
    return SparkSession.builder \
        .appName("Hadoop Data Processing") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

def load_and_clean_data(spark, input_path):
    """Charge et nettoie les données"""
    # Lecture des données
    df = spark.read.csv(input_path, header=True, inferSchema=True)
    
    # Nettoyage des données
    df = df.dropDuplicates(['client_id'])
    df = df.na.drop()
    
    return df

def process_customer_data(df):
    """Traite les données client et génère des features"""
    
    # Conversion des catégories en features numériques
    df = df.withColumn("genre_numeric", 
                      when(col("genre") == "M", 1).otherwise(0))
    
    # Création des features pour le clustering
    assembler = VectorAssembler(
        inputCols=["age", "montant_achat", "genre_numeric"],
        outputCol="features"
    )
    
    # Normalisation des features
    scaler = StandardScaler(
        inputCol="features",
        outputCol="scaled_features",
        withStd=True,
        withMean=True
    )
    
    # Application des transformations
    df = assembler.transform(df)
    df = scaler.fit(df).transform(df)
    
    return df

def perform_clustering(df, k=3):
    """Effectue le clustering des clients"""
    kmeans = KMeans(
        featuresCol="scaled_features",
        predictionCol="cluster",
        k=k,
        seed=42
    )
    
    model = kmeans.fit(df)
    df = model.transform(df)
    
    return df, model

def generate_customer_segments(df):
    """Génère des segments de clients basés sur le clustering"""
    
    # Analyse des segments
    segment_analysis = df.groupBy("cluster") \
        .agg(
            count("*").alias("nombre_clients"),
            avg("age").alias("age_moyen"),
            avg("montant_achat").alias("montant_moyen"),
            collect_list("segment_client").alias("segments")
        )
    
    return segment_analysis

def save_results(df, segment_analysis, output_path):
    """Sauvegarde les résultats du traitement"""
    
    # Sauvegarde des données traitées
    df.write.mode("overwrite").parquet(f"{output_path}/processed_data")
    
    # Sauvegarde de l'analyse des segments
    segment_analysis.write.mode("overwrite").parquet(f"{output_path}/segment_analysis")
    
    # Sauvegarde des statistiques
    stats = df.groupBy("cluster") \
        .agg(
            count("*").alias("nombre_clients"),
            avg("montant_achat").alias("montant_moyen"),
            stddev("montant_achat").alias("ecart_type_montant")
        )
    
    stats.write.mode("overwrite").parquet(f"{output_path}/cluster_stats")

def main():
    # Configuration des chemins
    input_path = "hdfs:///user/data/raw/sample_data.csv"
    output_path = "hdfs:///user/data/processed"
    
    # Création de la session Spark
    spark = create_spark_session()
    
    try:
        # Chargement et nettoyage des données
        print("Chargement des données...")
        df = load_and_clean_data(spark, input_path)
        
        # Traitement des données
        print("Traitement des données...")
        df = process_customer_data(df)
        
        # Clustering
        print("Application du clustering...")
        df, model = perform_clustering(df)
        
        # Analyse des segments
        print("Génération des segments...")
        segment_analysis = generate_customer_segments(df)
        
        # Sauvegarde des résultats
        print("Sauvegarde des résultats...")
        save_results(df, segment_analysis, output_path)
        
        # Affichage des statistiques
        print("\n=== Statistiques de traitement ===")
        print(f"Nombre total de clients : {df.count()}")
        print(f"Nombre de segments : {df.select('cluster').distinct().count()}")
        
        # Affichage des caractéristiques des segments
        segment_analysis.show()
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 