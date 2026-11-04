import sys
import pygame
from game import BLANC, NOIR, VIDE, OthelloGame
from ai import OthelloAI

# Initialisation de Pygame
pygame.init()

#dimensions de la fenêtre
TAILLE_CASE = 80
LARGEUR = 8 * TAILLE_CASE
HAUTEUR_BANDEAU = 60
HAUTEUT_TOTAL = LARGEUR + HAUTEUR_BANDEAU

# Palettes de couleurs
VERT_PLATEAU = (34, 139, 34)
VERT_LIGNE = (20, 100, 20)
NOIR_PION = (20, 20, 20)
BLANC_PION = (240, 240, 240)
ROUGE_HINT = (200, 50, 50)
GRIS_BANDEAU = (40, 40, 40)

ECRAN = pygame.display.set_mode((LARGEUR, HAUTEUT_TOTAL))
pygame.display.set_caption("Othello IA - TP")
POLICE = pygame.font.SysFont("Arial", 22, bold=True)

def dessiner_bandeau(jeu):
    """Affiche le score actuel et le joueur actif."""
    pygame.draw.rect(ECRAN, GRIS_BANDEAU, (0, 0, LARGEUR, HAUTEUR_BANDEAU))
    score_noir, score_blanc = jeu.calculer_score()
    
    texte_score = f"NOIR: {score_noir}  |  BLANC: {score_blanc}"
    surface_score = POLICE.render(texte_score, True, BLANC_PION)
    ECRAN.blit(surface_score, (20, 15))
    
    tour_texte = "NOIR" if jeu.joueur_actif == NOIR else "BLANC"
    couleur_texte = NOIR_PION if jeu.joueur_actif == NOIR else BLANC_PION
    surface_tour = POLICE.render(f"Tour : {tour_texte}", True, couleur_texte)
    ECRAN.blit(surface_tour, (LARGEUR - 160, 15))

def dessiner_plateau(jeu):
    """Dessine la grille, les pions et les coups valides."""
    ECRAN.fill(VERT_PLATEAU)
    
    for l in range(8):
        for c in range(8):
            y = l * TAILLE_CASE + HAUTEUR_BANDEAU
            x = c * TAILLE_CASE
            rect = pygame.Rect(x, y, TAILLE_CASE, TAILLE_CASE)
            pygame.draw.rect(ECRAN, VERT_LIGNE, rect, 2)
            
            pion = jeu.plateau[l][c]
            centre = (x + TAILLE_CASE // 2, y + TAILLE_CASE // 2)
            if pion == NOIR:
                pygame.draw.circle(ECRAN, NOIR_PION, centre, TAILLE_CASE // 2 - 6)
            elif pion == BLANC:
                pygame.draw.circle(ECRAN, BLANC_PION, centre, TAILLE_CASE // 2 - 6)

    # Petits points rouges sur les coups valides
    for l, c in jeu.obtenir_coups_valides(jeu.joueur_actif):
        y = l * TAILLE_CASE + HAUTEUR_BANDEAU + TAILLE_CASE // 2
        x = c * TAILLE_CASE + TAILLE_CASE // 2
        pygame.draw.circle(ECRAN, ROUGE_HINT, (x, y), 6)

def principal():
    jeu = OthelloGame()
    ia = OthelloAI(strategie="mixte", profondeur_max=3)
    horloge = pygame.time.Clock()
    en_cours = True

    while en_cours:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                en_cours = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if jeu.joueur_actif == NOIR:
                    pos_x, pos_y = event.pos
                    if pos_y >= HAUTEUR_BANDEAU:
                        colonne = pos_x // TAILLE_CASE
                        ligne = (pos_y - HAUTEUR_BANDEAU) // TAILLE_CASE

                        if jeu.est_coup_valide(ligne, colonne, NOIR):
                            jeu.jouer_coup(ligne, colonne, NOIR)
                            jeu.changer_joueur()

        # Tour de l'IA (Joueur BLANC)
        if jeu.joueur_actif == BLANC and not jeu.est_termine():
            dessiner_plateau(jeu)
            dessiner_bandeau(jeu)
            pygame.display.flip()
            pygame.time.wait(300)  # Délai court pour simuler la réflexion

            coup = ia.obtenir_meilleur_coup(jeu, BLANC)
            if coup:
                jeu.jouer_coup(coup[0], coup[1], BLANC)
            jeu.changer_joueur()

        # Gestion des cas où un joueur doit passer son tour
        if not jeu.obtenir_coups_valides(jeu.joueur_actif) and not jeu.est_termine():
            jeu.changer_joueur()

        dessiner_plateau(jeu)
        dessiner_bandeau(jeu)
        pygame.display.flip()
        horloge.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    principal()