#!/usr/bin/env python3

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pyspark.sql import SparkSession
import os
from pyspark.sql.functions import *

def load_processed_data(file_path):
    """Charge les données traitées depuis le fichier JSON."""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)

def analyze_customer_spending(df):
    """Analyse les dépenses des clients par catégorie."""
    # Analyse des dépenses moyennes par catégorie
    category_analysis = df.groupby('category').agg({
        'total_amount': ['mean', 'sum', 'count'],
        'purchase_count': 'mean'
    }).round(2)
    
    print("\nAnalyse des dépenses par catégorie:")
    print(category_analysis)
    
    # Visualisation
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='category', y='total_amount')
    plt.title('Dépenses moyennes par catégorie')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('category_spending.png')

def analyze_customer_behavior(df):
    """Analyse le comportement d'achat des clients."""
    # Top 10 des clients par montant total
    top_customers = df.nlargest(10, 'total_amount')
    
    print("\nTop 10 des clients par montant total:")
    print(top_customers[['customer_id', 'category', 'total_amount', 'purchase_count']])
    
    # Visualisation
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=df, x='purchase_count', y='total_amount', hue='category')
    plt.title('Relation entre nombre d\'achats et montant total')
    plt.tight_layout()
    plt.savefig('customer_behavior.png')

def generate_report(df):
    """Génère un rapport complet d'analyse."""
    print("=== Rapport d'analyse des données clients ===")
    print(f"Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Nombre total de transactions: {len(df)}")
    print(f"Nombre de catégories: {df['category'].nunique()}")
    print(f"Nombre de clients uniques: {df['customer_id'].nunique()}")
    
    analyze_customer_spending(df)
    analyze_customer_behavior(df)
    
    # Sauvegarde des statistiques dans un fichier
    stats = {
        'total_transactions': len(df),
        'unique_categories': df['category'].nunique(),
        'unique_customers': df['customer_id'].nunique(),
        'average_spending': df['total_amount'].mean(),
        'max_spending': df['total_amount'].max(),
        'min_spending': df['total_amount'].min()
    }
    
    with open('analysis_stats.json', 'w') as f:
        json.dump(stats, f, indent=4)

def create_spark_session():
    """Crée une session Spark pour l'analyse"""
    return SparkSession.builder \
        .appName("Hadoop Data Analysis") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

def load_processed_data(spark, input_path):
    """Charge les données traitées"""
    return spark.read.parquet(input_path)

def analyze_customer_segments(df):
    """Analyse détaillée des segments de clients"""
    
    # Conversion en pandas pour la visualisation
    segment_stats = df.groupBy("cluster") \
        .agg(
            count("*").alias("nombre_clients"),
            avg("age").alias("age_moyen"),
            avg("montant_achat").alias("montant_moyen"),
            stddev("montant_achat").alias("ecart_type_montant")
        ).toPandas()
    
    return segment_stats

def generate_visualizations(segment_stats, output_path):
    """Génère des visualisations pour l'analyse"""
    
    # Création du dossier de sortie
    os.makedirs(output_path, exist_ok=True)
    
    # 1. Distribution des clients par segment
    plt.figure(figsize=(10, 6))
    sns.barplot(data=segment_stats, x="cluster", y="nombre_clients")
    plt.title("Distribution des clients par segment")
    plt.xlabel("Segment")
    plt.ylabel("Nombre de clients")
    plt.savefig(f"{output_path}/segment_distribution.png")
    plt.close()
    
    # 2. Caractéristiques des segments
    plt.figure(figsize=(12, 6))
    segment_stats_melted = pd.melt(
        segment_stats,
        id_vars=["cluster"],
        value_vars=["age_moyen", "montant_moyen"],
        var_name="metric",
        value_name="value"
    )
    sns.barplot(data=segment_stats_melted, x="cluster", y="value", hue="metric")
    plt.title("Caractéristiques des segments")
    plt.savefig(f"{output_path}/segment_characteristics.png")
    plt.close()

def generate_report(segment_stats, output_path):
    """Génère un rapport d'analyse au format HTML"""
    
    html_content = f"""
    <html>
    <head>
        <title>Rapport d'Analyse des Segments Client</title>
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
        <h1>Rapport d'Analyse des Segments Client</h1>
        
        <h2>Statistiques par Segment</h2>
        {segment_stats.to_html()}
        
        <h2>Distribution des Clients</h2>
        <img src="segment_distribution.png" alt="Distribution des segments">
        
        <h2>Caractéristiques des Segments</h2>
        <img src="segment_characteristics.png" alt="Caractéristiques des segments">
        
        <h2>Recommandations</h2>
        <ul>
            <li>Segment 0: Clients à forte valeur - Stratégie de fidélisation premium</li>
            <li>Segment 1: Clients moyens - Programmes de fidélité standard</li>
            <li>Segment 2: Nouveaux clients - Stratégie d'acquisition et d'éducation</li>
        </ul>
    </body>
    </html>
    """
    
    with open(f"{output_path}/rapport_analyse.html", "w") as f:
        f.write(html_content)

def main():
    # Configuration des chemins
    input_path = "hdfs:///user/data/processed/processed_data"
    output_path = "hdfs:///user/data/analysis"
    local_output = "reports"
    
    # Création de la session Spark
    spark = create_spark_session()
    
    try:
        # Chargement des données
        print("Chargement des données traitées...")
        df = load_processed_data(spark, input_path)
        
        # Analyse des segments
        print("Analyse des segments...")
        segment_stats = analyze_customer_segments(df)
        
        # Génération des visualisations
        print("Génération des visualisations...")
        generate_visualizations(segment_stats, local_output)
        
        # Génération du rapport
        print("Génération du rapport...")
        generate_report(segment_stats, local_output)
        
        print("\n=== Analyse terminée ===")
        print(f"Le rapport a été généré dans : {local_output}/rapport_analyse.html")
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 