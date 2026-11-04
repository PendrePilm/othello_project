import math
from game import BLANC, NOIR, VIDE, OthelloGame

# Matrice de poids pour la stratégie POSITIONNELLE
# Les coins valent très cher (100), les cases adjacentes aux coins sont pénalisées (-20, -50)
MATRICE_POIDS = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,   1,   1,   1,   1,  -2,  10],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [ 10,  -2,   1,   1,   1,   1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
]

class OthelloAI:
    def __init__(self, strategie="mixte", profondeur_max=3):
        self.strategie = strategie
        self.profondeur_max = profondeur_max
        self.noeuds_explores = 0  # Compteur utile pour les statistiques du rapport

    # --- FONCTIONS D'ÉVALUATION ---

    def eval_absolue(self, plateau, joueur):
        """Évaluation basée uniquement sur le nombre de pions."""
        score_noir = sum(ligne.count(NOIR) for ligne in plateau)
        score_blanc = sum(ligne.count(BLANC) for ligne in plateau)
        diff = score_noir - score_blanc
        return diff if joueur == NOIR else -diff

    def eval_positionnelle(self, plateau, joueur):
        """Évaluation basée sur la valeur stratégique des cases de la grille."""
        score = 0
        for l in range(8):
            for c in range(8):
                if plateau[l][c] == joueur:
                    score += MATRICE_POIDS[l][c]
                elif plateau[l][c] == -joueur:
                    score -= MATRICE_POIDS[l][c]
        return score

    def eval_mobilite(self, jeu, plateau, joueur):
        """Évaluation axée sur le nombre de coups possibles (liberté d'action)."""
        coups_joueur = len(jeu.obtenir_coups_valides(joueur, plateau))
        coups_adversaire = len(jeu.obtenir_coups_valides(-joueur, plateau))
        return (coups_joueur - coups_adversaire) * 10

    def evaluer(self, jeu, plateau, joueur):
        """Sélectionne la fonction d'évaluation selon la stratégie configurée."""
        if self.strategie == "absolu":
            return self.eval_absolue(plateau, joueur)
        elif self.strategie == "positionnel":
            return self.eval_positionnelle(plateau, joueur)
        elif self.strategie == "mobilite":
            return self.eval_mobilite(jeu, plateau, joueur)
        elif self.strategie == "mixte":
            # Adapter l'évaluation selon l'avancement de la partie
            pions_poses = sum(case != VIDE for ligne in plateau for case in ligne)
            if pions_poses <= 25:      # Début de partie : contrôle des cases
                return self.eval_positionnelle(plateau, joueur)
            elif pions_poses <= 50:    # Milieu de partie : mobilité
                return self.eval_mobilite(jeu, plateau, joueur)
            else:                      # Fin de partie : maximiser les pions
                return self.eval_absolue(plateau, joueur)
        return 0

    # --- ALGORITHME ALPHA-BÊTA ---

    def alphabeta(self, jeu, plateau, profondeur, alpha, beta, est_max, joueur_ia):
        self.noeuds_explores += 1

        joueur_courant = joueur_ia if est_max else -joueur_ia
        coups_valides = jeu.obtenir_coups_valides(joueur_courant, plateau)

        # Condition d'arrêt : profondeur 0 ou fin de partie
        if profondeur == 0 or (not coups_valides and not jeu.obtenir_coups_valides(-joueur_courant, plateau)):
            return self.evaluer(jeu, plateau, joueur_ia), None

        # Si le joueur actif n'a pas de coup valide, il passe son tour
        if not coups_valides:
            valeur, _ = self.alphabeta(jeu, plateau, profondeur - 1, alpha, beta, not est_max, joueur_ia)
            return valeur, None

        meilleur_coup = None

        if est_max:
            valeur_max = -math.inf
            for l, c in coups_valides:
                # Simuler le coup sur une copie du plateau
                nouveau_plateau = [ligne[:] for ligne in plateau]
                jeu.jouer_coup(l, c, joueur_ia, nouveau_plateau)

                valeur, _ = self.alphabeta(jeu, nouveau_plateau, profondeur - 1, alpha, beta, False, joueur_ia)
                if valeur > valeur_max:
                    valeur_max = valeur
                    meilleur_coup = (l, c)

                alpha = max(alpha, valeur_max)
                if beta <= alpha:
                    break  # Coupure Alpha
            return valeur_max, meilleur_coup
        else:
            valeur_min = math.inf
            for l, c in coups_valides:
                nouveau_plateau = [ligne[:] for ligne in plateau]
                jeu.jouer_coup(l, c, -joueur_ia, nouveau_plateau)

                valeur, _ = self.alphabeta(jeu, nouveau_plateau, profondeur - 1, alpha, beta, True, joueur_ia)
                if valeur < valeur_min:
                    valeur_min = valeur
                    meilleur_coup = (l, c)

                beta = min(beta, valeur_min)
                if beta <= alpha:
                    break  # Coupure Bêta
            return valeur_min, meilleur_coup

    def obtenir_meilleur_coup(self, jeu, joueur_ia):
        """Calcule et renvoie le meilleur coup trouvé par l'IA."""
        self.noeuds_explores = 0
        _, coup = self.alphabeta(jeu, jeu.plateau, self.profondeur_max, -math.inf, math.inf, True, joueur_ia)
        return coup