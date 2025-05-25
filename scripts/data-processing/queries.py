from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def create_spark_session():
    """Crée une session Spark pour l'analyse"""
    return SparkSession.builder \
        .appName("Hadoop Data Analysis") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

def analyze_customer_value(spark, input_path):
    """Analyse de la valeur client (RFM Analysis)"""
    
    # Chargement des données
    df = spark.read.parquet(input_path)
    
    # Calcul des métriques RFM
    rfm = df.groupBy("client_id") \
        .agg(
            max("date_achat").alias("dernier_achat"),
            count("*").alias("frequence"),
            sum("montant_achat").alias("montant_total")
        )
    
    # Calcul de la recence (en jours)
    current_date = current_date()
    rfm = rfm.withColumn("recence", datediff(current_date, col("dernier_achat")))
    
    # Segmentation RFM
    rfm = rfm.withColumn("r_score", 
        when(col("recence") <= 30, 5)
        .when(col("recence") <= 60, 4)
        .when(col("recence") <= 90, 3)
        .when(col("recence") <= 180, 2)
        .otherwise(1))
    
    rfm = rfm.withColumn("f_score",
        when(col("frequence") >= 10, 5)
        .when(col("frequence") >= 7, 4)
        .when(col("frequence") >= 5, 3)
        .when(col("frequence") >= 3, 2)
        .otherwise(1))
    
    rfm = rfm.withColumn("m_score",
        when(col("montant_total") >= 1000, 5)
        .when(col("montant_total") >= 750, 4)
        .when(col("montant_total") >= 500, 3)
        .when(col("montant_total") >= 250, 2)
        .otherwise(1))
    
    # Calcul du score RFM global
    rfm = rfm.withColumn("rfm_score", 
        (col("r_score") + col("f_score") + col("m_score")) / 3)
    
    return rfm

def analyze_purchase_patterns(spark, input_path):
    """Analyse des patterns d'achat"""
    
    df = spark.read.parquet(input_path)
    
    # Analyse par jour de la semaine
    patterns = df.withColumn("jour_semaine", dayofweek("date_achat")) \
        .groupBy("jour_semaine") \
        .agg(
            count("*").alias("nombre_achats"),
            avg("montant_achat").alias("montant_moyen"),
            sum("montant_achat").alias("montant_total")
        )
    
    # Analyse par heure de la journée
    hourly_patterns = df.withColumn("heure", hour("date_achat")) \
        .groupBy("heure") \
        .agg(
            count("*").alias("nombre_achats"),
            avg("montant_achat").alias("montant_moyen")
        )
    
    return patterns, hourly_patterns

def analyze_product_categories(spark, input_path):
    """Analyse des catégories de produits"""
    
    df = spark.read.parquet(input_path)
    
    # Analyse des catégories les plus populaires
    category_analysis = df.groupBy("categorie_produit") \
        .agg(
            count("*").alias("nombre_achats"),
            sum("montant_achat").alias("revenu_total"),
            avg("montant_achat").alias("montant_moyen")
        )
    
    # Analyse des combinaisons de catégories
    window_spec = Window.partitionBy("client_id").orderBy("date_achat")
    df = df.withColumn("categorie_precedente", lag("categorie_produit").over(window_spec))
    
    category_combinations = df.filter(col("categorie_precedente").isNotNull()) \
        .groupBy("categorie_precedente", "categorie_produit") \
        .count() \
        .orderBy(desc("count"))
    
    return category_analysis, category_combinations

def analyze_customer_loyalty(spark, input_path):
    """Analyse de la fidélité client"""
    
    df = spark.read.parquet(input_path)
    
    # Calcul de la durée de relation client
    customer_loyalty = df.groupBy("client_id") \
        .agg(
            min("date_achat").alias("premier_achat"),
            max("date_achat").alias("dernier_achat"),
            count("*").alias("nombre_achats"),
            sum("montant_achat").alias("montant_total")
        )
    
    customer_loyalty = customer_loyalty.withColumn(
        "duree_relation", 
        datediff(col("dernier_achat"), col("premier_achat"))
    )
    
    # Analyse de la rétention
    retention = customer_loyalty.groupBy(
        year("premier_achat").alias("annee_acquisition")
    ).agg(
        count("*").alias("nouveaux_clients"),
        avg("duree_relation").alias("duree_moyenne_relation"),
        avg("nombre_achats").alias("nombre_moyen_achats")
    )
    
    return customer_loyalty, retention

def generate_insights_report(spark, input_path, output_path):
    """Génère un rapport complet d'analyse"""
    
    # Création du dossier de sortie
    os.makedirs(output_path, exist_ok=True)
    
    # Exécution des analyses
    print("Analyse de la valeur client...")
    rfm_analysis = analyze_customer_value(spark, input_path)
    
    print("Analyse des patterns d'achat...")
    patterns, hourly_patterns = analyze_purchase_patterns(spark, input_path)
    
    print("Analyse des catégories de produits...")
    category_analysis, category_combinations = analyze_product_categories(spark, input_path)
    
    print("Analyse de la fidélité client...")
    customer_loyalty, retention = analyze_customer_loyalty(spark, input_path)
    
    # Génération des visualisations
    print("Génération des visualisations...")
    
    # 1. Distribution des scores RFM
    rfm_pd = rfm_analysis.toPandas()
    plt.figure(figsize=(10, 6))
    sns.histplot(data=rfm_pd, x="rfm_score", bins=20)
    plt.title("Distribution des scores RFM")
    plt.savefig(f"{output_path}/rfm_distribution.png")
    plt.close()
    
    # 2. Patterns d'achat par heure
    hourly_pd = hourly_patterns.toPandas()
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=hourly_pd, x="heure", y="nombre_achats")
    plt.title("Nombre d'achats par heure")
    plt.savefig(f"{output_path}/hourly_patterns.png")
    plt.close()
    
    # 3. Top catégories de produits
    category_pd = category_analysis.toPandas()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=category_pd, x="categorie_produit", y="revenu_total")
    plt.title("Revenu total par catégorie")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_path}/category_revenue.png")
    plt.close()
    
    # Génération du rapport HTML
    print("Génération du rapport...")
    
    html_content = f"""
    <html>
    <head>
        <title>Rapport d'Analyse des Données Client</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ max-width: 100%; height: auto; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Rapport d'Analyse des Données Client</h1>
        
        <h2>Analyse RFM</h2>
        {rfm_pd.describe().to_html()}
        <img src="rfm_distribution.png" alt="Distribution RFM">
        
        <h2>Patterns d'Achat</h2>
        {hourly_pd.to_html()}
        <img src="hourly_patterns.png" alt="Patterns horaires">
        
        <h2>Analyse des Catégories</h2>
        {category_pd.to_html()}
        <img src="category_revenue.png" alt="Revenu par catégorie">
        
        <h2>Insights Clés</h2>
        <ul>
            <li>Segmentation RFM : Identification des clients les plus précieux</li>
            <li>Patterns d'achat : Optimisation des horaires de promotion</li>
            <li>Catégories de produits : Focus sur les catégories les plus rentables</li>
            <li>Fidélité client : Analyse de la rétention et de la durée de relation</li>
        </ul>
    </body>
    </html>
    """
    
    with open(f"{output_path}/rapport_insights.html", "w") as f:
        f.write(html_content)
    
    print(f"\nRapport généré avec succès dans : {output_path}/rapport_insights.html")

def main():
    # Configuration des chemins
    input_path = "hdfs:///user/data/processed/processed_data"
    output_path = "reports/insights"
    
    # Création de la session Spark
    spark = create_spark_session()
    
    try:
        # Génération du rapport d'analyse
        generate_insights_report(spark, input_path, output_path)
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 