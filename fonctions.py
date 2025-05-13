"""
Ce fichier contient les fonctions principales pour le projet de lecture de codes-barres par lancers aléatoires de rayons.
Il regroupe les fonctions précédemment séparées pour une meilleure intégration.
"""

# Modules standards
import os
import random

# Modules scientifiques
import numpy as np
from scipy.signal import convolve2d
from skimage import color, io
from skimage.morphology import closing, opening, square
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu
from scipy.ndimage import map_coordinates

# Fonctions de segmentation
def segmentation(image_path):
    """
    Segmente une image pour identifier la zone contenant un code-barres.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        
    Returns:
        tuple: (min_row, min_col, max_row, max_col) délimitant la région d'intérêt
    """
    # Chargement de l'image
    img = io.imread(image_path)
    if img.shape[-1] == 4:  # Si l'image a un canal alpha
        img = img[..., :3]  # Supprimer le canal alpha
    I = color.rgb2gray(img)
    
    # Paramètres
    sigma_noise = 0.02
    sigma_G = 1.8
    sigma_T = 18
    seuil_coherence = 0.3
    
    # Ajout de bruit
    bruit = np.random.normal(0, sigma_noise, I.shape)
    I_bruite = np.clip(I + bruit, 0, 1)
    
    # Calcul des gradients
    size = int(3 * sigma_G)
    x, y = np.meshgrid(np.arange(-size, size+1), np.arange(-size, size+1))
    G_x = -(x / (2 * np.pi * sigma_G**4)) * np.exp(-(x**2 + y**2) / (2*sigma_G**2))
    G_y = -(y / (2 * np.pi * sigma_G**4)) * np.exp(-(x**2 + y**2) / (2*sigma_G**2))
    
    I_x = convolve2d(I_bruite, G_x, mode='same', boundary='symm')
    I_y = convolve2d(I_bruite, G_y, mode='same', boundary='symm')
    
    norme = np.sqrt(I_x**2 + I_y**2) + 1e-8
    I_x /= norme
    I_y /= norme
    
    # Tenseur de structure
    size_T = int(2 * sigma_T)
    G = (1 / (2 * np.pi * sigma_T**2)) * np.exp(-(x**2 + y**2) / (2 * sigma_T**2))
    
    T_xx = convolve2d(I_x**2, G, mode='same', boundary='symm')
    T_xy = convolve2d(I_x * I_y, G, mode='same', boundary='symm')
    T_yy = convolve2d(I_y**2, G, mode='same', boundary='symm')
    
    # Calcul de cohérence D1
    D1 = 1 - np.sqrt((T_xx - T_yy)**2 + 4*(T_xy**2)) / (T_xx + T_yy + 1e-15)
    
    # Segmentation
    M = (D1 > seuil_coherence).astype(int)
    
    # Nettoyage morphologique
    M_clean = closing(M, square(3))
    M_clean = opening(M_clean, square(2))
    
    # Extraction de la plus grande région
    labels = label(M_clean)
    if labels.max() > 0:
        regions = regionprops(labels)
        largest_region = max(regions, key=lambda r: r.area)
        return largest_region.bbox  # (min_row, min_col, max_row, max_col)
    else:
        raise ValueError("Aucune région cohérente détectée.")

# Fonctions de lancer de rayons
def point_aleatoire_segment(P1, P2):
    """
    Génère un point aléatoire sur un segment [P1, P2].
    
    Args:
        P1 (tuple): Premier point du segment (x, y)
        P2 (tuple): Deuxième point du segment (x, y)
        
    Returns:
        tuple: Point aléatoire sur le segment (x, y)
    """
    t = np.random.random()
    return (P1[0] + t * (P2[0] - P1[0]), P1[1] + t * (P2[1] - P1[1]))

def lancer_aleatoire(C1, C2, C3, C4):
    """
    Génère un rayon aléatoire ou orienté dans une zone délimitée par 4 coins.
    
    Paramètres:
        C1, C2, C3, C4 (tuple): Coordonnées des coins de la région (x, y).
        
    Retourne:
        (tuple): Coordonnées des points de départ et d'arrivée du rayon.
    """
    # Calculer la direction principale
    direction = np.array([C2[0] - C1[0], C2[1] - C1[1]])
    direction = direction / np.linalg.norm(direction)
    
    # Angle maximum autorisé (30 degrés)
    angle_max = np.pi/6
    
    essais = 0
    while essais <= 100:
        essais += 1
        
        # Choisir des points aléatoires sur des segments opposés
        if np.random.random() < 0.5:
            p1 = point_aleatoire_segment(C1, C4)
            p2 = point_aleatoire_segment(C2, C3)
        else:
            p1 = point_aleatoire_segment(C2, C3)
            p2 = point_aleatoire_segment(C1, C4)
        
        # Calculer la direction du rayon
        rayon = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        norm_rayon = np.linalg.norm(rayon)
        if norm_rayon == 0:
            continue
            
        rayon = rayon / norm_rayon
        
        # Calculer l'angle avec la direction principale
        cos_angle = abs(np.dot(rayon, direction))
        angle = np.arccos(cos_angle)
        
        # Si l'angle est inférieur à la limite, retourner le rayon
        if angle < angle_max:
            return p1, p2
    
    # Si aucun rayon adéquat n'a été trouvé, retourner le dernier généré
    return p1, p2

# Fonctions d'extraction
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

# Fonctions de décodage
def decode_ean13_signature(binary_signature):
    """
    Decoder un code-barres EAN-13 à partir de sa signature binaire.
    
    Paramètres:
        binary_signature: liste d'entiers (0 ou 1), représentant la signature binaire du code-barres (95 bits)
            
    Retourne:
        code_barres: chaîne de caractères représentant le code EAN-13 décodé
    """
    # Vérifier la longueur de la signature
    if len(binary_signature) != 95:
        raise ValueError("La signature binaire doit contenir exactement 95 bits.")
    
    # Motifs de garde
    guard_left = [1, 0, 1]
    guard_center = [0, 1, 0, 1, 0]
    guard_right = [1, 0, 1]
    
    # Vérifier les motifs de garde
    if list(binary_signature[0:3]) != guard_left:
        raise ValueError("Motif de garde gauche incorrect.")
    if list(binary_signature[45:50]) != guard_center:
        raise ValueError("Motif de garde central incorrect.")
    if list(binary_signature[92:95]) != guard_right:
        raise ValueError("Motif de garde droit incorrect.")
    
    # Tables de codage pour les chiffres
    code_L = {
        '0001101': '0',
        '0011001': '1',
        '0010011': '2',
        '0111101': '3',
        '0100011': '4',
        '0110001': '5',
        '0101111': '6',
        '0111011': '7',
        '0110111': '8',
        '0001011': '9',
    }
    code_G = {
        '0100111': '0',
        '0110011': '1',
        '0011011': '2',
        '0100001': '3',
        '0011101': '4',
        '0111001': '5',
        '0000101': '6',
        '0010001': '7',
        '0001001': '8',
        '0010111': '9',
    }
    code_R = {
        '1110010': '0',
        '1100110': '1',
        '1101100': '2',
        '1000010': '3',
        '1011100': '4',
        '1001110': '5',
        '1010000': '6',
        '1000100': '7',
        '1001000': '8',
        '1110100': '9',
    }
    
    # Table de parité pour déterminer le premier chiffre
    parity_table = {
        'LLLLLL': '0',
        'LLGLGG': '1',
        'LLGGLG': '2',
        'LLGGGL': '3',
        'LGLLGG': '4',
        'LGGLLG': '5',
        'LGGGLL': '6',
        'LGLGLG': '7',
        'LGLGGL': '8',
        'LGGLGL': '9',
    }
    
    # Décodage des 6 chiffres de gauche
    left_digits = []
    parity_pattern = ''
    for i in range(6):
        start = 3 + i * 7
        end = start + 7
        pattern_bits = binary_signature[start:end]
        pattern = ''.join(map(str, pattern_bits))
        if pattern in code_L:
            digit = code_L[pattern]
            parity_pattern += 'L'
        elif pattern in code_G:
            digit = code_G[pattern]
            parity_pattern += 'G'
        else:
            raise ValueError(f"Motif inconnu dans la partie gauche : {pattern}")
        left_digits.append(digit)
    
    # Déterminer le premier chiffre à partir du motif de parité
    if parity_pattern in parity_table:
        first_digit = parity_table[parity_pattern]
    else:
        raise ValueError(f"Motif de parité inconnu : {parity_pattern}")
    
    # Décodage des 6 chiffres de droite
    right_digits = []
    for i in range(6):
        start = 50 + i * 7
        end = start + 7
        pattern_bits = binary_signature[start:end]
        pattern = ''.join(map(str, pattern_bits))
        if pattern in code_R:
            digit = code_R[pattern]
        else:
            raise ValueError(f"Motif inconnu dans la partie droite : {pattern}")
        right_digits.append(digit)
    
    # Construire le code-barres complet
    code_barres = first_digit + ''.join(left_digits) + ''.join(right_digits)
    
    # Vérifier la clé de contrôle
    digits = list(map(int, code_barres))
    if len(digits) != 13:
        raise ValueError("Le code-barres doit contenir 13 chiffres.")
    
    # Calcul de la clé de contrôle selon la norme EAN-13
    # Étape 1 : Somme des chiffres en positions paires (2e, 4e, ..., 12e)
    sum_even = sum(digits[i] for i in range(1, 12, 2))
    # Étape 2 : Multiplier la somme par 3
    sum_even *= 3
    # Étape 3 : Somme des chiffres en positions impaires (1ère, 3e, ..., 11e)
    sum_odd = sum(digits[i] for i in range(0, 12, 2))
    # Étape 4 : Calculer le total
    total = sum_even + sum_odd
    # Étape 5 : Calculer la clé de contrôle
    check_digit = (10 - (total % 10)) % 10
    
    # Vérifier si la clé de contrôle est correcte
    if check_digit != digits[-1]:
        raise ValueError(f"Clé de contrôle invalide : attendu {check_digit}, obtenu {digits[-1]}")
    
    return code_barres