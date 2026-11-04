"""Règles d'Othello indépendantes de l'interface et des algorithmes d'IA."""

from __future__ import annotations

VIDE = 0
NOIR = 1
BLANC = -1

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


class OthelloGame:
    """Plateau 8x8. Dans ce TP, les blancs commencent (consigne du sujet)."""

    def __init__(self) -> None:
        self.plateau = [[VIDE for _ in range(8)] for _ in range(8)]
        self.plateau[3][3] = self.plateau[4][4] = BLANC
        self.plateau[3][4] = self.plateau[4][3] = NOIR
        self.joueur_actif = BLANC

    @staticmethod
    def est_sur_plateau(l: int, c: int) -> bool:
        return 0 <= l < 8 and 0 <= c < 8

    def copier(self) -> OthelloGame:
        autre = OthelloGame()
        autre.plateau = [ligne[:] for ligne in self.plateau]
        autre.joueur_actif = self.joueur_actif
        return autre

    def calculer_score(self, plateau: list[list[int]] | None = None) -> tuple[int, int]:
        if plateau is None:
            plateau = self.plateau
        return (sum(ligne.count(NOIR) for ligne in plateau),
                sum(ligne.count(BLANC) for ligne in plateau))

    def nombre_cases_vides(self, plateau: list[list[int]] | None = None) -> int:
        if plateau is None:
            plateau = self.plateau
        return sum(ligne.count(VIDE) for ligne in plateau)

    def nombre_coups_joues(self, plateau: list[list[int]] | None = None) -> int:
        # Chaque coup posé occupe exactement une nouvelle case, même s'il retourne des pions.
        return 60 - self.nombre_cases_vides(plateau)

    def obtenir_pions_a_retourner(
        self, l: int, c: int, joueur: int, plateau: list[list[int]] | None = None
    ) -> list[tuple[int, int]]:
        if plateau is None:
            plateau = self.plateau
        if not self.est_sur_plateau(l, c) or plateau[l][c] != VIDE:
            return []

        captures = []
        adversaire = -joueur
        for dl, dc in DIRECTIONS:
            a_retourner = []
            i, j = l + dl, c + dc
            while self.est_sur_plateau(i, j) and plateau[i][j] == adversaire:
                a_retourner.append((i, j))
                i += dl
                j += dc
            if a_retourner and self.est_sur_plateau(i, j) and plateau[i][j] == joueur:
                captures.extend(a_retourner)
        return captures

    def est_coup_valide(
        self, l: int, c: int, joueur: int, plateau: list[list[int]] | None = None
    ) -> bool:
        return bool(self.obtenir_pions_a_retourner(l, c, joueur, plateau))

    def obtenir_coups_valides(
        self, joueur: int, plateau: list[list[int]] | None = None
    ) -> list[tuple[int, int]]:
        if plateau is None:
            plateau = self.plateau
        return [(l, c) for l in range(8) for c in range(8)
                if plateau[l][c] == VIDE and self.est_coup_valide(l, c, joueur, plateau)]

    def jouer_coup(
        self, l: int, c: int, joueur: int, plateau: list[list[int]] | None = None
    ) -> bool:
        if plateau is None:
            plateau = self.plateau
        captures = self.obtenir_pions_a_retourner(l, c, joueur, plateau)
        if not captures:
            return False
        plateau[l][c] = joueur
        for i, j in captures:
            plateau[i][j] = joueur
        return True

    def changer_joueur(self) -> None:
        self.joueur_actif = -self.joueur_actif

    def est_termine(self, plateau: list[list[int]] | None = None) -> bool:
        if plateau is None:
            plateau = self.plateau
        return (not self.obtenir_coups_valides(NOIR, plateau)
                and not self.obtenir_coups_valides(BLANC, plateau))

    def passer_si_necessaire(self) -> bool:
        """Passe le tour si nécessaire ; renvoie True si un passage a eu lieu."""
        if self.obtenir_coups_valides(self.joueur_actif):
            return False
        if self.est_termine():
            return False
        self.changer_joueur()
        return True


if __name__ == "__main__":
    jeu = OthelloGame()
    print("Premier joueur :", "Blanc" if jeu.joueur_actif == BLANC else "Noir")
    print("Coups légaux :", jeu.obtenir_coups_valides(jeu.joueur_actif))
