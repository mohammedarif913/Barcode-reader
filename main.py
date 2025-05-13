import os
from utils.segmentation import segmentation
from utils.rays import lancer_aleatoire
from utils.extraction import extract_signature
from utils.decoder import decode_ean13_signature

def main():
    """
    Programme principal :
    1. Charge une image fournie par l'utilisateur.
    2. Effectue la segmentation pour détecter la région d'intérêt.
    3. Lance des rayons aléatoires pour extraire des signatures.
    4. Tente de décoder le code-barres EAN-13 jusqu'à réussir ou atteindre la limite.
    """
    # Demande à l'utilisateur de fournir un chemin d'image valide
    image_path = input("Veuillez entrer le chemin du fichier image : ")
    while not os.path.exists(image_path):
        print("Fichier introuvable. Veuillez réessayer.")
        image_path = input("Veuillez entrer un chemin valide : ")

    # Étape 1 : Segmentation pour détecter la région d'intérêt
    try:
        min_row, min_col, max_row, max_col = segmentation(image_path)
        print("Segmentation réussie. Région détectée.")
    except Exception as e:
        print(f"Erreur lors de la segmentation : {e}")
        return

    # Définir les coins de la région détectée
    p1 = (min_col, min_row)
    p2 = (max_col, min_row)
    p3 = (max_col, max_row)
    p4 = (min_col, max_row)

    # Étape 2 : Recherche d'un code-barres en lançant des rayons aléatoires
    max_attempts = 20  # Limite d'essais
    attempt = 0
    code_barres = None
    while attempt < max_attempts:
        print(f"Tentative {attempt + 1}/{max_attempts}...")
        # Générer un rayon aléatoire
        point1, point2 = lancer_aleatoire(p1, p2, p3, p4)
        # Extraire la signature le long du rayon généré
        signature_95bits = extract_signature(image_path, point1, point2)
        if signature_95bits is not None:
            try:
                # Tenter de décoder la signature
                code_barres = decode_ean13_signature(signature_95bits)
                print(f"Code-barres détecté : {code_barres}")
                break  # Arrêter la boucle si un code valide est trouvé
            except ValueError as e:
                print(f"Erreur de décodage : {e}")
        else:
            print("Signature non valide ou non extraite correctement.")
        attempt += 1

    # Étape 3 : Résultat final
    if code_barres:
        print(f"Code-barres final détecté : {code_barres}")
    else:
        print("Échec de la détection après plusieurs tentatives.")

if __name__ == "__main__":
    main()