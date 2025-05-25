#!/usr/bin/env python3

import os
import time
import json
import logging
from datetime import datetime
import psutil
import requests
from flask import Flask, render_template, jsonify
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from prometheus_client import start_http_server, Gauge, Counter
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cluster_monitor.log'),
        logging.StreamHandler()
    ]
)

class ClusterMonitor:
    def __init__(self):
        self.app = Flask(__name__)
        self.metrics = {
            'cpu_usage': Gauge('hadoop_cpu_usage', 'CPU Usage per node'),
            'memory_usage': Gauge('hadoop_memory_usage', 'Memory Usage per node'),
            'disk_usage': Gauge('hadoop_disk_usage', 'Disk Usage per node'),
            'active_nodes': Gauge('hadoop_active_nodes', 'Number of active nodes'),
            'failed_tasks': Counter('hadoop_failed_tasks', 'Number of failed tasks'),
            'data_processed': Counter('hadoop_data_processed', 'Amount of data processed')
        }
        
        # Configuration des seuils d'alerte
        self.alert_thresholds = {
            'cpu_usage': 80,  # 80% CPU
            'memory_usage': 85,  # 85% Memory
            'disk_usage': 90,  # 90% Disk
            'failed_tasks': 5  # 5 tâches échouées
        }
        
        # Historique des métriques
        self.metrics_history = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'tasks': []
        }

    def collect_metrics(self):
        """Collecte les métriques du cluster Hadoop"""
        try:
            # Collecte des métriques système
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Mise à jour des métriques Prometheus
            self.metrics['cpu_usage'].set(cpu_percent)
            self.metrics['memory_usage'].set(memory.percent)
            self.metrics['disk_usage'].set(disk.percent)
            
            # Ajout à l'historique
            self.metrics_history['cpu'].append(cpu_percent)
            self.metrics_history['memory'].append(memory.percent)
            self.metrics_history['disk'].append(disk.percent)
            
            # Vérification des seuils d'alerte
            self.check_alerts(cpu_percent, memory.percent, disk.percent)
            
            logging.info(f"Metrics collected - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {str(e)}")

    def check_alerts(self, cpu, memory, disk):
        """Vérifie les seuils d'alerte et envoie des notifications"""
        alerts = []
        
        if cpu > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {cpu}%")
        if memory > self.alert_thresholds['memory_usage']:
            alerts.append(f"High Memory usage: {memory}%")
        if disk > self.alert_thresholds['disk_usage']:
            alerts.append(f"High Disk usage: {disk}%")
            
        if alerts:
            self.send_alert(alerts)

    def send_alert(self, alerts):
        """Envoie des alertes via différents canaux"""
        alert_message = "\n".join(alerts)
        logging.warning(f"ALERT: {alert_message}")
        
        # Ici, vous pouvez ajouter l'envoi d'alertes par email, Slack, etc.
        # Exemple avec Slack:
        # self.send_slack_alert(alert_message)

    def create_dashboard(self):
        """Crée un dashboard interactif avec Plotly"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('CPU Usage', 'Memory Usage', 'Disk Usage', 'Task Status')
        )
        
        # Graphique CPU
        fig.add_trace(
            go.Scatter(y=self.metrics_history['cpu'], name='CPU'),
            row=1, col=1
        )
        
        # Graphique Memory
        fig.add_trace(
            go.Scatter(y=self.metrics_history['memory'], name='Memory'),
            row=1, col=2
        )
        
        # Graphique Disk
        fig.add_trace(
            go.Scatter(y=self.metrics_history['disk'], name='Disk'),
            row=2, col=1
        )
        
        # Mise à jour du layout
        fig.update_layout(
            title='Hadoop Cluster Monitoring Dashboard',
            height=800,
            showlegend=True
        )
        
        return fig

    def start_monitoring(self):
        """Démarre le monitoring du cluster"""
        # Démarrer le serveur Prometheus
        start_http_server(8000)
        
        # Démarrer la collecte des métriques en arrière-plan
        threading.Thread(target=self.collect_metrics_loop, daemon=True).start()
        
        # Démarrer le serveur Flask
        self.app.run(host='0.0.0.0', port=5000)

    def collect_metrics_loop(self):
        """Boucle de collecte des métriques"""
        while True:
            self.collect_metrics()
            time.sleep(60)  # Collecte toutes les minutes

    @app.route('/')
    def dashboard():
        """Route pour le dashboard"""
        fig = self.create_dashboard()
        return render_template('dashboard.html', plot=fig.to_html())

    @app.route('/metrics')
    def metrics():
        """Route pour les métriques au format JSON"""
        return jsonify({
            'cpu': self.metrics_history['cpu'][-1],
            'memory': self.metrics_history['memory'][-1],
            'disk': self.metrics_history['disk'][-1]
        })

def main():
    monitor = ClusterMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 