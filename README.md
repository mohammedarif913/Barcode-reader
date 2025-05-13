README.md
markdown# Lecture de Codes-Barres par Lancers Aléatoires de Rayons

Un système de détection et de décodage de codes-barres EAN-13 à partir d'images, utilisant une approche de tracé de rayons aléatoires.

## Description
Ce projet implémente une solution complète pour la lecture de codes-barres EAN-13 à partir d'images numériques. L'approche repose sur:
- La segmentation pour détecter les régions d'intérêt
- L'analyse par tenseur de structure pour identifier l'orientation
- Des lancers aléatoires de rayons pour simuler un scanner laser
- L'extraction de signatures binaires et le décodage selon le standard EAN-13

## Installation
```bash
pip install -r requirements.txt
Utilisation
bashpython main.py  # Version ligne de commande
python app.py   # Interface graphique


### requirements.txt
numpy==1.22.3
scipy==1.8.0
matplotlib==3.5.1
scikit-image==0.19.2
opencv-python==4.5.5.64
Pillow==9.0.1

### .gitignore
Byte-compiled / optimized / DLL files
pycache/
*.py[cod]
*$py.class
Distribution / packaging
dist/
build/
*.egg-info/
Virtual environments
venv/
env/
.env/
IDE specific files
.idea/
.vscode/
*.swp
*.swo
OS specific files
.DS_Store
Thumbs.db
Output files
.png
.jpg
.jpeg
!data/barcodes/.png
!data/barcodes/.jpg
!data/barcodes/.jpeg

C'est maintenant terminé. Vous avez tous les fichiers nécessaires pour commencer votre projet GitHub. Vous pouvez créer les fichiers et dossiers avec les commandes que j'ai fournies au début, puis copier le contenu pour chaque fichier.
