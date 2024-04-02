from flask import Flask, jsonify
from os import getpid
import socket
import json
import threading
import queue

app = Flask(__name__)

# File de tâches pour traiter les données de géolocalisation de manière asynchrone
location_data_queue = queue.Queue()

# Fonction pour traiter les données de géolocalisation de manière asynchrone
def process_location_data():
    while True:
        location_data = location_data_queue.get()
        # Traitement des données de géolocalisation ici
        print("Données de géolocalisation traitées:", location_data)

# Démarrer le thread de traitement des données de géolocalisation
processing_thread = threading.Thread(target=process_location_data)
processing_thread.daemon = True
processing_thread.start()

@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.get_json()
    location_data_queue.put(data)
    return jsonify({"status": "success"})

# Configuration du serveur TCP/IP
SERVER_HOST = '127.0.0.1'  # Adresse IP du serveur
SERVER_PORT = 65432        # Port sur lequel écouter les connexions

# Fonction pour gérer les connexions TCP/IP
def handle_tcp_connections():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permettre la réutilisation de l'adresse
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen()
        print("Attente de connexions TCP/IP...")
        while True:
            conn, addr = server_socket.accept()
            print("Connecté par", addr, " Process ID: ", getpid())
            # Démarrer un thread pour gérer la connexion
            threading.Thread(target=handle_client, args=(conn, addr)).start()

# Fonction pour gérer chaque connexion client
def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)  # Recevoir les données de géolocalisation
            if not data:
                break
            data = json.loads(data.decode())  # Convertir les données JSON
            print("Données de géolocalisation reçues de", addr, ":", data)
            location_data_queue.put(data)  # Mettre les données dans la file d'attente pour traitement asynchrone
    except (ConnectionResetError, socket.timeout) as e:
        print("Connexion avec", addr, "fermée de manière inattendue :", e)
    finally:
        conn.close()

if __name__ == '__main__':
    # Démarrer le serveur TCP/IP dans un thread séparé
    tcp_thread = threading.Thread(target=handle_tcp_connections)
    tcp_thread.daemon = True
    tcp_thread.start()
    # Démarrer le serveur Flask
    app.run(debug=False)
