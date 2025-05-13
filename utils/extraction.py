import numpy as np
from skimage import io, color
from skimage.filters import threshold_otsu
from scipy.ndimage import map_coordinates

def extract_signature(image_path, p1, p2):
    """
    Extrait une signature binaire de 95 bits le long d'un rayon défini par deux points.
    
    Paramètres:
        image_path (str): Chemin de l'image
        p1 (tuple): Point de départ du rayon (x, y)
        p2 (tuple): Point d'arrivée du rayon (x, y)
        
    Retourne:
        list: Liste de 95 bits représentant la signature extraite
    """
    # Charger l'image
    img = io.imread(image_path)
    if img.shape[-1] == 4:  # Si l'image a un canal alpha
        img = img[..., :3]
    image = color.rgb2gray(img)
    
    # Étape 1 : Calcul de la longueur du rayon
    longueur_rayon = int(np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2))
    print(f"Longueur du rayon : {longueur_rayon} pixels")
    
    # Étape 2 : Extraction initiale de la signature
    nb_points = max(longueur_rayon, 95)  # Nombre de points à échantillonner
    t = np.linspace(0, 1, nb_points)     # Paramètre d'interpolation
    
    # Calcul des coordonnées du rayon
    x = p1[0] + (p2[0] - p1[0]) * t
    y = p1[1] + (p2[1] - p1[1]) * t
    
    # Extraction des intensités sur le rayon avec interpolation bilinéaire
    intensities = map_coordinates(image, [y, x], order=1, mode='reflect')
    
    # Étape 3 : Application du seuil d'Otsu
    threshold = threshold_otsu(intensities)  # Calcul du seuil d'Otsu
    binary_signature = (intensities > threshold).astype(int)  # Binarisation
    
    # Étape 4 : Trouver les limites utiles
    non_zero = np.nonzero(binary_signature)[0]
    if len(non_zero) == 0:
        print("Aucune région utile trouvée dans la signature.")
        return None  # Retourne None si aucune donnée utile
    
    # Étape 5 : Réduction aux indices utiles
    start_idx = non_zero[0]
    end_idx = non_zero[-1]
    
    # Coordonnées des points utiles
    t_start = start_idx / nb_points
    t_end = end_idx / nb_points
    useful_p1 = (
        p1[0] + (p2[0] - p1[0]) * t_start,
        p1[1] + (p2[1] - p1[1]) * t_start
    )
    useful_p2 = (
        p1[0] + (p2[0] - p1[0]) * t_end,
        p1[1] + (p2[1] - p1[1]) * t_end
    )
    
    # Étape 6 : Ajustement et extraction finale
    useful_length = np.sqrt((useful_p2[0] - useful_p1[0])**2 + (useful_p2[1] - useful_p1[1])**2)
    u = max(1, int(useful_length / 95))  # Calcul de l'unité de base
    print(f"Unité de base u calculée : {u}")
    
    # Étape 7 : Extraction finale sur 95 * u points
    nb_points_final = 95 * u
    t = np.linspace(0, 1, nb_points_final)
    x = useful_p1[0] + (useful_p2[0] - useful_p1[0]) * t
    y = useful_p1[1] + (useful_p2[1] - useful_p1[1]) * t
    
    # Extraction finale avec interpolation
    final_signature = map_coordinates(image, [y, x], order=1, mode='reflect')
    
    # Binarisation finale avec Otsu
    final_threshold = threshold_otsu(final_signature)
    final_binary_signature = (final_signature > final_threshold).astype(int)
    
    # Étape 8 : Sélection des 95 premiers bits
    if len(final_binary_signature) >= 95:
        signature_95bits = final_binary_signature[:95]
        return signature_95bits  # Retourne la signature binaire
    else:
        print("La signature extraite est trop courte.")
        return None