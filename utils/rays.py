import numpy as np

def lancer_aleatoire(C1, C2, C3, C4):
    """
    Génère un rayon aléatoire ou orienté dans une zone délimitée par 4 coins.
    
    Paramètres:
        C1, C2, C3, C4 (tuple): Coordonnées des coins de la région (x, y).
        
    Retourne:
        (tuple): Coordonnées des points de départ et d'arrivée du rayon.
    """
    # Vérification des coordonnées
    if not all(len(point) == 2 for point in [C1, C2, C3, C4]):
        raise ValueError("Tous les points doivent avoir deux coordonnées (x, y).")
    
    # Calculer la direction principale
    direction = np.array([C2[0] - C1[0], C2[1] - C1[1]])
    direction = direction / np.linalg.norm(direction)
    
    # Angle maximum autorisé (30 degrés)
    angle_max = np.pi/6
    
    # Essayer de générer un rayon respectant la contrainte d'angle
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