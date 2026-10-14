# Constant pour l'etat des cases 
from ast import If


VIDE = 0
NOIR = 1 # Joueur 1
BLANC = -1 #Joueur 2

class OthelloGame :

    def __init__(self):
        # Crée la grille  8*8 vide
        self.plateau = [[VIDE for _ in range(8)] for _ in range(8)]

        # Place les pions de départ
        self.plateau[3][3], self.plateau[4][4] = BLANC, BLANC
        self.plateau[3][4], self.plateau[4][3] = NOIR, NOIR

        self.joueur_actif = NOIR  # Le joueur noir commence

    def est_sur_plateau(self, l, c):
        # Vérifie si les coordonnées sont sur le plateau
        if 0 <= l < 8 and 0 <= c < 8:
            return True
        else:
            return False

    def calculer_score(self, plateau=None):
        if plateau is None:
            plateau = self.plateau

        # Calcule le score pour chaque joueur

        score_noir = sum(row.count(NOIR) for row in plateau)
        score_blanc = sum(row.count(BLANC) for row in plateau)
        return score_noir, score_blanc

if __name__ == "__main__":
    jeu = OthelloGame()
    print("Plateau créé avec succès ! ")
    score_noir, score_blanc = jeu.calculer_score()
    print(f"Score Noir: {score_noir}, Score Blanc: {score_blanc}")