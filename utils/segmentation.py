import numpy as np
from scipy.signal import convolve2d
from skimage import color, io
from skimage.morphology import closing, opening, square
from skimage.measure import label, regionprops

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