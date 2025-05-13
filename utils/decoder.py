def decode_ean13_signature(binary_signature):
    """
    Decoder un code-barres EAN-13 à partir de sa signature binaire.
    
    Paramètres:
        binary_signature: liste d'entiers (0 ou 1), représentant la signature
            binaire du code-barres (95 bits)
            
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