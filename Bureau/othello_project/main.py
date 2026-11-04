"""Interface Pygame : humain contre IA ou IA contre IA.

Lancer avec --help pour choisir couleur, stratégie, algorithme et budget temps.
"""

from __future__ import annotations

import argparse

from ai import ALGORITHMES, STRATEGIES, OthelloAI
from game import BLANC, NOIR, OthelloGame

TAILLE_CASE = 80
LARGEUR = 8 * TAILLE_CASE
HAUTEUR_BANDEAU = 76
HAUTEUR_TOTALE = LARGEUR + HAUTEUR_BANDEAU
VERT_PLATEAU = (34, 139, 34)
VERT_LIGNE = (20, 100, 20)
NOIR_PION = (20, 20, 20)
BLANC_PION = (240, 240, 240)
ROUGE_HINT = (200, 50, 50)
GRIS_BANDEAU = (40, 40, 40)


def principal() -> None:
    parser = argparse.ArgumentParser(description="Othello : humain contre IA ou IA contre IA")
    parser.add_argument("--mode", choices=("humain-ia", "ia-ia"), default="humain-ia")
    parser.add_argument("--humain", choices=("blanc", "noir"), default="blanc")
    parser.add_argument("--strategie-blanc", choices=STRATEGIES, default="mixte")
    parser.add_argument("--strategie-noir", choices=STRATEGIES, default="mixte")
    parser.add_argument("--algo-blanc", choices=ALGORITHMES, default="alphabeta")
    parser.add_argument("--algo-noir", choices=ALGORITHMES, default="alphabeta")
    parser.add_argument("--profondeur", type=int, default=2)
    parser.add_argument("--temps", type=float, default=1.0)
    args = parser.parse_args()

    try:
        import pygame
    except ImportError as exc:
        raise SystemExit("Pygame est requis pour l'interface : pip install -r requirements.txt") from exc

    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR_TOTALE))
    pygame.display.set_caption("Othello - IA / Fondements de l'IA")
    police = pygame.font.SysFont("Arial", 21, bold=True)
    sous_police = pygame.font.SysFont("Arial", 17)

    jeu = OthelloGame()
    humain = BLANC if args.humain == "blanc" else NOIR
    ia_blanc = OthelloAI(args.strategie_blanc, args.profondeur, args.algo_blanc, args.temps)
    ia_noir = OthelloAI(args.strategie_noir, args.profondeur, args.algo_noir, args.temps)
    # Deux objets distincts = mémoires/transpositions de recherche séparées.
    horloge = pygame.time.Clock()
    en_cours = True

    def dessiner() -> None:
        ecran.fill(VERT_PLATEAU)
        pygame.draw.rect(ecran, GRIS_BANDEAU, (0, 0, LARGEUR, HAUTEUR_BANDEAU))
        score_noir, score_blanc = jeu.calculer_score()
        texte = police.render(f"BLANC : {score_blanc}   |   NOIR : {score_noir}", True, BLANC_PION)
        ecran.blit(texte, (14, 8))
        if jeu.est_termine():
            resultat = "Blanc gagne" if score_blanc > score_noir else (
                "Noir gagne" if score_noir > score_blanc else "Égalité")
            info = f"Fin de partie — {resultat}  (fermez la fenêtre)"
        else:
            info = f"Au tour des {'BLANCS' if jeu.joueur_actif == BLANC else 'NOIRS'}"
        ecran.blit(sous_police.render(info, True, BLANC_PION), (14, 42))
        for l in range(8):
            for c in range(8):
                x = c * TAILLE_CASE
                y = l * TAILLE_CASE + HAUTEUR_BANDEAU
                pygame.draw.rect(ecran, VERT_LIGNE, (x, y, TAILLE_CASE, TAILLE_CASE), 2)
                pion = jeu.plateau[l][c]
                if pion != 0:
                    couleur = BLANC_PION if pion == BLANC else NOIR_PION
                    pygame.draw.circle(ecran, couleur,
                                       (x + TAILLE_CASE // 2, y + TAILLE_CASE // 2),
                                       TAILLE_CASE // 2 - 6)
        tour_humain = args.mode == "humain-ia" and jeu.joueur_actif == humain
        if tour_humain and not jeu.est_termine():
            for l, c in jeu.obtenir_coups_valides(jeu.joueur_actif):
                pygame.draw.circle(ecran, ROUGE_HINT,
                                   (c * TAILLE_CASE + TAILLE_CASE // 2,
                                    l * TAILLE_CASE + HAUTEUR_BANDEAU + TAILLE_CASE // 2), 6)
        pygame.display.flip()

    try:
        while en_cours:
            for evenement in pygame.event.get():
                if evenement.type == pygame.QUIT:
                    en_cours = False
                if (evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1
                        and not jeu.est_termine() and args.mode == "humain-ia"
                        and jeu.joueur_actif == humain):
                    x, y = evenement.pos
                    l, c = (y - HAUTEUR_BANDEAU) // TAILLE_CASE, x // TAILLE_CASE
                    if jeu.jouer_coup(l, c, humain):
                        jeu.changer_joueur()
            if not en_cours:
                break
            if not jeu.est_termine():
                jeu.passer_si_necessaire()
            dessiner()
            if not jeu.est_termine() and (args.mode == "ia-ia" or jeu.joueur_actif != humain):
                ia = ia_blanc if jeu.joueur_actif == BLANC else ia_noir
                coup = ia.obtenir_meilleur_coup(jeu, jeu.joueur_actif)
                if coup is not None:
                    assert jeu.jouer_coup(*coup, jeu.joueur_actif)
                    jeu.changer_joueur()
                else:
                    jeu.passer_si_necessaire()
            horloge.tick(30)
    finally:
        pygame.quit()


if __name__ == "__main__":
    principal()
