# Constant pour l'etat des cases 
from ast import If


VIDE = 0
NOIR = 1 # Joueur 1
BLANC = -1 #Joueur 2

Direction = [(-1, -1), (-1, 0), (-1, 1),
             (0, -1),          (0, 1),
             (1, -1), (1, 0), (1, 1)    ]

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

    def obtenir_pions_a_retourner(self, l, c, joueur, plateau=None):
        if plateau is None:
            plateau = self.plateau

        pions_a_retourner = []

        # Vérifie si la case est vide   
        if plateau[l][c] != VIDE:
            return []

        adversaire = -joueur
        pions_a_retourner = []

        # On test chacune des directions
        for dl, dc in Direction:
            pions_dans_dir = []
            cur_l, cur_c = l + dl, c + dc

            # Tant que l'on rencontre des pions adverses, on les ajoute à la liste temporaire
            while self.est_sur_plateau(cur_l, cur_c) and plateau[cur_l][cur_c] == adversaire:
                pions_dans_dir.append((cur_l, cur_c))
                cur_l += dl
                cur_c += dc

            # Si la liste de pions se termine par un pion du joueur -> Capture !
            if self.est_sur_plateau(cur_l, cur_c) and plateau[cur_l][cur_c] == joueur:
                pions_a_retourner.extend(pions_dans_dir)

        return pions_a_retourner

    def est_coup_valide(self, l, c, joueur, plateau=None):
        # Le coup est valide si la case est vide et qu'il y a au moins un pion à retourner
        if plateau is None:
            plateau = self.plateau
        return len(self.obtenir_pions_a_retourner(l, c, joueur, plateau)) > 0

    
    def obtenir_coups_valides(self, joueur, plateau=None):
        # Parcours le plateau et renvoie la liste des cases (l, c) jouables
        if plateau is None:
            plateau = self.plateau

        coups = []
        for l in range(8):
            for c in range(8):
                if self.est_coup_valide(l, c, joueur, plateau):
                    coups.append((l, c))
        return coups


if __name__ == "__main__":
    jeu = OthelloGame()
    coups_noir = jeu.obtenir_coups_valides(NOIR)
    print ("Au debut du jeu, le joueur noir peut jouer :", coups_noir)