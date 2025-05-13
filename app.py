import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from utils.segmentation import segmentation
from utils.extraction import extract_signature
from utils.rays import lancer_aleatoire
from utils.decoder import decode_ean13_signature

class BarcodeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lecteur de Code-Barres")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.resizable(True, True)
        
        # Dégradé de fond
        self.canvas = tk.Canvas(self, width=1200, height=800)
        self.canvas.pack(fill="both", expand=True)
        self.create_gradient()
        
        # Variables
        self.image = None
        self.image_path = ""
        self.binary_signature = None
        self.decoded_barcode = None
        
        # Créer l'interface
        self.setup_ui()
    
    def create_gradient(self):
        """Créer un dégradé de fond."""
        for i in range(100):
            color = f"#{i:02x}{i:02x}{255-i:02x}"
            self.canvas.create_rectangle(0, i * 9, 1200, (i + 1) * 3, fill=color, outline="")
    
    def setup_ui(self):
        """Créer les widgets de l'interface."""
        self.frame = tk.Frame(self.canvas)
        self.frame.place(relx=0.5, rely=0.05, anchor="n")
        
        # Bouton pour charger une image
        self.load_button = tk.Button(self.frame, text="Charger une image", 
                                    command=self.load_image, fg="black", font=("Arial", 12))
        self.load_button.grid(row=0, column=0, padx=10, pady=5)
        
        # Boutons pour sélectionner le mode
        self.mode_var = tk.StringVar(value="manuel")
        tk.Radiobutton(self.frame, text="Rayon Manuel", variable=self.mode_var, 
                      value="manuel", font=("Arial", 12)).grid(row=0, column=1, padx=10)
        tk.Radiobutton(self.frame, text="Rayons Aléatoires", variable=self.mode_var, 
                      value="aleatoire", font=("Arial", 12)).grid(row=0, column=2, padx=10)
        
        # Boutons pour les actions
        self.segment_button = tk.Button(self.frame, text="Segmentation", 
                                      command=self.segment_image, fg="black", font=("Arial", 12))
        self.segment_button.grid(row=0, column=3, padx=10, pady=5)
        
        self.extract_button = tk.Button(self.frame, text="Extraction", 
                                      command=self.extract_signature, fg="black", font=("Arial", 12))
        self.extract_button.grid(row=0, column=4, padx=10, pady=5)
        
        self.decode_button = tk.Button(self.frame, text="Decoder", 
                                     command=self.decode_barcode, fg="black", font=("Arial", 12))
        self.decode_button.grid(row=0, column=5, padx=10, pady=5)
        
        self.verify_button = tk.Button(self.frame, text="Vérifier dans la base", 
                                     command=self.verify_database, fg="black", font=("Arial", 12))
        self.verify_button.grid(row=0, column=6, padx=10, pady=5)
        
        # Bouton de réinitialisation
        self.reset_button = tk.Button(self.frame, text="Réinitialiser", 
                                    command=self.reset_app, fg="black", font=("Arial", 12))
        self.reset_button.grid(row=0, column=7, padx=10, pady=5)
        
        # Zone d'affichage d'image
        self.image_label = tk.Label(self.canvas, bg="#ffffff", bd=2, relief="sunken")
        self.image_label.place(relx=0.5, rely=0.6, anchor="center", width=800, height=500)
        
        # Zone de feedback
        self.feedback = tk.Label(self, text="Prêt", font=("Arial", 12), bg="#e9ecef", fg="black")
        self.feedback.place(relx=0.5, rely=0.95, anchor="s")
        
        # Ajouter un label en bas à droite
        footer_label = tk.Label(self, text="Projet Image TS225 2024/2025", font=("Arial", 14), fg="white")
        footer_label.place(relx=1.0, rely=1.0, anchor="se", x=0, y=0)
        
        footer_label2 = tk.Label(self, text="Développé par: Mehdi, Salma, Arif et Louriz", 
                              font=("Arial", 14), fg="white")
        footer_label2.place(relx=0.0, rely=1.0, anchor="sw", x=0, y=0)
        
        # Bouton pour quitter l'application
        self.quit_button = tk.Button(
            self,
            text="Quitter",
            command=self.quit_app,
            fg="red",
            bg="red", 
            font=("Arial", 12, "bold"),
            relief="raised",
            bd=2,
            padx=10,
            pady=5
        )
        self.quit_button.place(relx=0.5, rely=0.975, anchor="center")
    
    def load_image(self):
        """Charger une image depuis le fichier."""
        try:
            file_path = filedialog.askopenfilename(
                title="Sélectionner une image",
                filetypes=[("Images", "*.png;*.jpg;*.jpeg")]
            )
            if not file_path:
                self.feedback.config(text="Aucune image sélectionnée.")
                return
            
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.display_image(self.image)
            self.feedback.config(text="Image chargée avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'image : {str(e)}")
            self.feedback.config(text="Erreur lors du chargement.")
    
    def display_image(self, img):
        """Afficher une image redimensionnée."""
        img = img.resize((800, 500))
        img = ImageTk.PhotoImage(img)
        self.image_label.config(image=img)
        self.image_label.image = img
    
    def segment_image(self):
        """Segmentation réelle avec extraction depuis le fichier segmentation."""
        try:
            # Mise à jour du feedback pour informer l'utilisateur
            self.feedback.config(text="Segmentation en cours...")
            self.update_idletasks()
            
            # Vérifier si une image est chargée
            if not self.image_path:
                messagebox.showerror("Erreur", "Aucune image chargée !")
                self.feedback.config(text="Erreur : Chargez une image.")
                return
                
            # Appel de la fonction de segmentation
            min_row, min_col, max_row, max_col = segmentation(self.image_path)
            
            # Stocker les coins détectés
            self.detected_region = [
                (min_col, min_row),  # C1
                (max_col, min_row),  # C2
                (max_col, max_row),  # C3
                (min_col, max_row)   # C4
            ]
            
            # Mise à jour du feedback
            self.feedback.config(text="Segmentation terminée.")
            
            # Afficher le rectangle détecté sur l'image
            img = Image.open(self.image_path)
            img_display = img.copy()
            # Implémenter l'affichage du rectangle ici
            
            self.display_image(img_display)
            
        except Exception as e:
            # Gestion des erreurs avec message d'alerte
            messagebox.showerror("Erreur", f"Erreur lors de la segmentation : {str(e)}")
            self.feedback.config(text="Erreur lors de la segmentation.")
    def extract_signature(self):
        """Extraction des signatures avec un rayon manuel ou aléatoire."""
        try:
            # Feedback initial
            self.feedback.config(text="Extraction en cours...")
            self.update_idletasks()
            
            # Vérifier si une image est chargée
            if not self.image_path:
                messagebox.showerror("Erreur", "Aucune image chargée !")
                self.feedback.config(text="Erreur : Chargez une image.")
                return
                
            # Vérifier si la segmentation a été réalisée (avec des coins détectés)
            if not hasattr(self, 'detected_region') or self.detected_region is None:
                messagebox.showerror("Erreur", "Aucune région détectée. Lancez la segmentation d'abord.")
                self.feedback.config(text="Erreur : Pas de région détectée.")
                return
                
            # Récupérer les coins détectés pour la zone d'intérêt
            C1, C2, C3, C4 = self.detected_region  # Coins détectés après segmentation
            
            # Vérifier le mode choisi (manuel ou aléatoire)
            if self.mode_var.get() == "manuel":
                messagebox.showinfo("Instruction", "Cliquez sur deux points pour définir un rayon.")
                self.feedback.config(text="Attente de la sélection manuelle...")
                self.points = []  # Réinitialiser les points pour la sélection manuelle
                self.canvas.bind("<Button-1>", self.on_click_manual)
                return
            elif self.mode_var.get() == "aleatoire":
                # Générer un rayon aléatoire avec la fonction lancer_aleatoire
                p1, p2 = lancer_aleatoire(C1, C2, C3, C4)
                points = (p1, p2)
                
                # Appeler la fonction d'extraction pour obtenir la signature binaire
                self.binary_signature = extract_signature(self.image_path, points[0], points[1])
                
                # Vérifier si l'extraction a réussi
                if self.binary_signature is None:
                    raise ValueError("Signature non extraite ou invalide.")
                    
                # Afficher la signature binaire extraite
                plt.figure()
                plt.step(range(len(self.binary_signature)), self.binary_signature, where='mid')
                plt.title("Signature binaire extraite")
                plt.xlabel("Position")
                plt.ylabel("Valeur (0 ou 1)")
                plt.grid(True)
                plt.show()
                
                # Mise à jour du feedback
                self.feedback.config(text="Extraction terminée avec succès.")
        except Exception as e:
            # Gestion des erreurs
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction : {str(e)}")
            self.feedback.config(text="Erreur lors de l'extraction.")
            
    def on_click_manual(self, event):
        """Gestion des clics pour le rayon manuel."""
        # Convertir les coordonnées du clic en coordonnées de l'image
        x, y = event.x, event.y
        self.points.append((x, y))
        
        # Afficher le point sur l'image
        img_display = self.image.copy()
        # Implémenter l'affichage des points et du rayon ici
        
        self.display_image(img_display)
        
        if len(self.points) == 1:
            self.feedback.config(text="Premier point sélectionné. Sélectionnez le second point.")
        elif len(self.points) == 2:
            self.feedback.config(text="Deux points sélectionnés. Traitement en cours...")
            self.canvas.unbind("<Button-1>")
            self.after(100, self.process_manual_extraction)
    
    def process_manual_extraction(self):
        """Traite l'extraction manuelle après sélection des points."""
        try:
            p1, p2 = self.points
            
            # Extraire la signature le long du rayon défini par les points
            self.binary_signature = extract_signature(self.image_path, p1, p2)
            
            # Vérifier si l'extraction a réussi
            if self.binary_signature is None:
                raise ValueError("Signature non extraite ou invalide.")
                
            # Afficher la signature binaire extraite
            plt.figure()
            plt.step(range(len(self.binary_signature)), self.binary_signature, where='mid')
            plt.title("Signature binaire extraite")
            plt.xlabel("Position")
            plt.ylabel("Valeur (0 ou 1)")
            plt.grid(True)
            plt.show()
            
            self.feedback.config(text="Extraction manuelle terminée avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction manuelle : {str(e)}")
            self.feedback.config(text="Erreur lors de l'extraction manuelle.")
    
    def decode_barcode(self):
        """Décodage en utilisant la fonction du fichier fonctions.py."""
        try:
            # Feedback pour l'utilisateur
            self.feedback.config(text="Décodage en cours...")
            self.update_idletasks()
            
            # Vérifier si une signature a été extraite
            if self.binary_signature is None:
                messagebox.showerror("Erreur", "Aucune signature disponible pour le décodage.")
                self.feedback.config(text="Erreur : Aucune signature détectée.")
                return
                
            # Appeler la fonction de décodage
            self.decoded_barcode = decode_ean13_signature(self.binary_signature)
            
            # Mise à jour du feedback avec le code-barres détecté
            self.feedback.config(text=f"Code-barres détecté : {self.decoded_barcode}")
            messagebox.showinfo("Décodage Réussi", f"Code-barres : {self.decoded_barcode}")
        except Exception as e:
            # Gestion des erreurs
            messagebox.showerror("Erreur", f"Erreur lors du décodage : {str(e)}")
            self.feedback.config(text="Erreur lors du décodage.")
    
    def verify_database(self):
        """Vérifier dans la base de données."""
        try:
            self.feedback.config(text="Vérification dans la base...")
            self.update_idletasks()
            
            # Vérifier si un code-barres a été décodé
            if not self.decoded_barcode:
                messagebox.showwarning("Attention", "Aucun code-barres décodé. Veuillez lancer le décodage d'abord.")
                self.feedback.config(text="Erreur : Pas de code-barres décodé.")
                return
                
            # Charger la base de données (fichier texte contenant une liste de codes-barres valides)
            database_path = filedialog.askopenfilename(
                title="Charger la base de données",
                filetypes=[("Fichiers texte", "*.txt")]
            )
            
            if not database_path:
                self.feedback.config(text="Erreur : Aucune base de données sélectionnée.")
                return
                
            # Lire la base de données
            with open(database_path, 'r') as file:
                database = [line.strip() for line in file.readlines()]
                
            # Vérifier si le code-barres est dans la base
            if self.decoded_barcode in database:
                messagebox.showinfo("Résultat", f"Produit trouvé : {self.decoded_barcode}")
                self.feedback.config(text="Produit trouvé dans la base.")
            else:
                messagebox.showwarning("Résultat", f"Produit non trouvé : {self.decoded_barcode}")
                self.feedback.config(text="Produit non trouvé dans la base.")
        except Exception as e:
            # Gestion des erreurs
            messagebox.showerror("Erreur", f"Erreur lors de la vérification : {str(e)}")
            self.feedback.config(text="Erreur lors de la vérification.")
    
    def reset_app(self):
        """Réinitialiser l'application."""
        self.image = None
        self.image_path = ""
        self.binary_signature = None
        self.decoded_barcode = None
        if hasattr(self, 'detected_region'):
            del self.detected_region
        self.image_label.config(image="")
        self.feedback.config(text="Réinitialisé.")
    
    def quit_app(self):
        """Quitter l'application."""
        plt.close('all')
        self.destroy()

if __name__ == "__main__":
    app = BarcodeApp()
    app.mainloop()