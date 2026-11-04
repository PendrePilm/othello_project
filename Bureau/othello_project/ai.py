"""Min-Max, Alpha-Bêta, NegaMax, approfondissement itératif et transpositions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from game import BLANC, NOIR, VIDE, OthelloGame

MATRICE_POIDS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100],
]
COINS = ((0, 0), (0, 7), (7, 0), (7, 7))
STRATEGIES = ("absolu", "positionnel", "mobilite", "mixte")
ALGORITHMES = ("minimax", "alphabeta", "negamax")
INF = math.inf
SCORE_VICTOIRE = 100_000
MAX_TRANSPOSITIONS = 100_000


class TimeoutRecherche(Exception):
    """Interruption contrôlée : le dernier résultat COMPLET reste valable."""


@dataclass(frozen=True)
class EntreeTransposition:
    profondeur: int
    score: float
    drapeau: Literal["EXACT", "INFERIEUR", "SUPERIEUR"]
    coup: tuple[int, int] | None


@dataclass
class StatistiquesRecherche:
    temps: float = 0.0
    noeuds: int = 0
    coupures: int = 0
    tt_hits: int = 0
    tt_stores: int = 0
    profondeur_atteinte: int = 0  # en demi-coups (plies)
    timeout: bool = False
    score: float | None = None
    coup: tuple[int, int] | None = None


class OthelloAI:
    """Moteur de recherche.

    profondeur_max=1 recherche deux demi-coups (joueur + adversaire),
    selon la convention particulière du sujet du TP.

    Une IA conserve sa propre table de transposition entre ses tours. Ne pas
    partager la même instance entre deux joueurs d'un match.
    """

    def __init__(
        self, strategie: str = "mixte", profondeur_max: int = 2,
        algorithme: str = "alphabeta", temps_max: float | None = 1.0,
        table_transposition: bool = True, tri_coups: bool = True,
    ) -> None:
        if strategie not in STRATEGIES:
            raise ValueError(f"Stratégie inconnue : {strategie}")
        if algorithme not in ALGORITHMES:
            raise ValueError(f"Algorithme inconnu : {algorithme}")
        if profondeur_max < 1:
            raise ValueError("La profondeur doit être >= 1")
        if temps_max is not None and temps_max <= 0:
            raise ValueError("Le temps_max doit être positif (ou None).")
        self.strategie = strategie
        self.profondeur_max = profondeur_max
        self.algorithme = algorithme
        self.temps_max = temps_max
        # Min-Max est volontairement sans cache/élagage pour être une référence claire.
        self.utiliser_tt = table_transposition and algorithme != "minimax"
        self.tri_coups = tri_coups
        self.table_transposition: dict[tuple, EntreeTransposition] = {}
        self.derniere_recherche = StatistiquesRecherche()
        self.noeuds_explores = 0
        self._deadline: float | None = None

    def vider_cache(self) -> None:
        self.table_transposition.clear()

    def eval_absolue(self, plateau: list[list[int]], joueur: int) -> float:
        noir = sum(ligne.count(NOIR) for ligne in plateau)
        blanc = sum(ligne.count(BLANC) for ligne in plateau)
        return float((noir - blanc) * joueur)

    def eval_positionnelle(self, plateau: list[list[int]], joueur: int) -> float:
        return float(sum(MATRICE_POIDS[l][c] * plateau[l][c] * joueur
                         for l in range(8) for c in range(8)))

    def eval_mobilite(self, jeu: OthelloGame, plateau: list[list[int]], joueur: int) -> float:
        mobilite = (len(jeu.obtenir_coups_valides(joueur, plateau))
                    - len(jeu.obtenir_coups_valides(-joueur, plateau)))
        coins = sum(plateau[l][c] * joueur for l, c in COINS)
        return float(10 * mobilite + 35 * coins)

    def evaluer(self, jeu: OthelloGame, plateau: list[list[int]], joueur: int) -> float:
        # Toujours privilégier une victoire certaine à un avantage heuristique.
        if jeu.est_termine(plateau):
            diff = self.eval_absolue(plateau, joueur)
            if diff > 0:
                return SCORE_VICTOIRE + diff
            if diff < 0:
                return -SCORE_VICTOIRE + diff
            return 0.0
        strategie = self.strategie
        if strategie == "mixte":
            # 20-25 premiers coups, puis mobilité ; fin sur les 10-16 dernières cases.
            if jeu.nombre_coups_joues(plateau) <= 25:
                strategie = "positionnel"
            elif jeu.nombre_cases_vides(plateau) <= 16:
                strategie = "absolu"
            else:
                strategie = "mobilite"
        if strategie == "absolu":
            return self.eval_absolue(plateau, joueur)
        if strategie == "positionnel":
            return self.eval_positionnelle(plateau, joueur)
        return self.eval_mobilite(jeu, plateau, joueur)

    def _verifier_temps(self) -> None:
        if self._deadline is not None and perf_counter() >= self._deadline:
            raise TimeoutRecherche

    def _coups_ordonnes(
        self, coups: list[tuple[int, int]],
        suggestion: tuple[int, int] | None = None,
    ) -> list[tuple[int, int]]:
        if not self.tri_coups:
            return coups
        return sorted(coups, key=lambda c: (c == suggestion, MATRICE_POIDS[c[0]][c[1]]),
                      reverse=True)

    @staticmethod
    def _cle(
        plateau: list[list[int]], joueur: int, joueur_racine: int, algorithme: str
    ) -> tuple:
        # Pour Min-Max / Alpha-Bêta, le score est relatif à joueur_racine.
        # Pour NegaMax, le score est relatif au joueur courant.
        return (tuple(tuple(ligne) for ligne in plateau), joueur,
                joueur_racine if algorithme != "negamax" else 0, algorithme)

    def _enregistrer(
        self, cle: tuple, profondeur: int, valeur: float,
        alpha_initial: float, beta_initial: float,
        coup: tuple[int, int] | None,
    ) -> None:
        if not self.utiliser_tt:
            return
        if valeur <= alpha_initial:
            drapeau: Literal["EXACT", "INFERIEUR", "SUPERIEUR"] = "SUPERIEUR"
        elif valeur >= beta_initial:
            drapeau = "INFERIEUR"
        else:
            drapeau = "EXACT"
        precedente = self.table_transposition.get(cle)
        if precedente is not None and precedente.profondeur > profondeur:
            return  # Ne pas remplacer un résultat plus profond par un moins précis.
        if precedente is None and len(self.table_transposition) >= MAX_TRANSPOSITIONS:
            self.table_transposition.pop(next(iter(self.table_transposition)))
        self.table_transposition[cle] = EntreeTransposition(profondeur, valeur, drapeau, coup)
        self.derniere_recherche.tt_stores += 1

    def _consulter(
        self, cle: tuple, profondeur: int, alpha: float, beta: float,
    ) -> tuple[float, float, tuple[float, tuple[int, int] | None] | None,
               tuple[int, int] | None]:
        if not self.utiliser_tt:
            return alpha, beta, None, None
        entree = self.table_transposition.get(cle)
        if entree is None:
            return alpha, beta, None, None
        suggestion = entree.coup
        if entree.profondeur < profondeur:
            return alpha, beta, None, suggestion
        self.derniere_recherche.tt_hits += 1
        if entree.drapeau == "EXACT":
            return alpha, beta, (entree.score, entree.coup), suggestion
        if entree.drapeau == "INFERIEUR":
            alpha = max(alpha, entree.score)
        else:
            beta = min(beta, entree.score)
        if alpha >= beta:
            return alpha, beta, (entree.score, entree.coup), suggestion
        return alpha, beta, None, suggestion

    def _minimax(
        self, jeu: OthelloGame, plateau: list[list[int]],
        profondeur: int, joueur: int, racine: int,
    ) -> tuple[float, tuple[int, int] | None]:
        self._verifier_temps()
        self.derniere_recherche.noeuds += 1
        coups = jeu.obtenir_coups_valides(joueur, plateau)
        if profondeur == 0:
            return self.evaluer(jeu, plateau, racine), None
        if not coups:
            if not jeu.obtenir_coups_valides(-joueur, plateau):
                return self.evaluer(jeu, plateau, racine), None
            valeur, _ = self._minimax(jeu, plateau, profondeur - 1, -joueur, racine)
            return valeur, None

        maximiser = joueur == racine
        meilleur_score = -INF if maximiser else INF
        meilleur_coup = None
        for coup in self._coups_ordonnes(coups):
            suite = [ligne[:] for ligne in plateau]
            jeu.jouer_coup(*coup, joueur, suite)
            score, _ = self._minimax(jeu, suite, profondeur - 1, -joueur, racine)
            if (maximiser and score > meilleur_score) or (not maximiser and score < meilleur_score):
                meilleur_score, meilleur_coup = score, coup
        return meilleur_score, meilleur_coup

    def _alphabeta(
        self, jeu: OthelloGame, plateau: list[list[int]], profondeur: int,
        alpha: float, beta: float, joueur: int, racine: int,
    ) -> tuple[float, tuple[int, int] | None]:
        self._verifier_temps()
        self.derniere_recherche.noeuds += 1
        alpha_initial, beta_initial = alpha, beta
        cle = self._cle(plateau, joueur, racine, "alphabeta")
        alpha, beta, connu, suggestion = self._consulter(cle, profondeur, alpha, beta)
        if connu is not None:
            return connu
        coups = jeu.obtenir_coups_valides(joueur, plateau)
        if profondeur == 0:
            valeur = self.evaluer(jeu, plateau, racine)
            self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, None)
            return valeur, None
        if not coups:
            if not jeu.obtenir_coups_valides(-joueur, plateau):
                valeur = self.evaluer(jeu, plateau, racine)
            else:
                valeur, _ = self._alphabeta(
                    jeu, plateau, profondeur - 1, alpha, beta, -joueur, racine)
            self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, None)
            return valeur, None

        maximiser = joueur == racine
        valeur = -INF if maximiser else INF
        meilleur_coup = None
        for coup in self._coups_ordonnes(coups, suggestion):
            suite = [ligne[:] for ligne in plateau]
            jeu.jouer_coup(*coup, joueur, suite)
            score, _ = self._alphabeta(
                jeu, suite, profondeur - 1, alpha, beta, -joueur, racine)
            if (maximiser and score > valeur) or (not maximiser and score < valeur):
                valeur, meilleur_coup = score, coup
            if maximiser:
                alpha = max(alpha, valeur)
            else:
                beta = min(beta, valeur)
            if alpha >= beta:
                self.derniere_recherche.coupures += 1
                break
        self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, meilleur_coup)
        return valeur, meilleur_coup

    def _negamax(
        self, jeu: OthelloGame, plateau: list[list[int]], profondeur: int,
        alpha: float, beta: float, joueur: int,
    ) -> tuple[float, tuple[int, int] | None]:
        self._verifier_temps()
        self.derniere_recherche.noeuds += 1
        alpha_initial, beta_initial = alpha, beta
        cle = self._cle(plateau, joueur, joueur, "negamax")
        alpha, beta, connu, suggestion = self._consulter(cle, profondeur, alpha, beta)
        if connu is not None:
            return connu
        coups = jeu.obtenir_coups_valides(joueur, plateau)
        if profondeur == 0:
            valeur = self.evaluer(jeu, plateau, joueur)
            self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, None)
            return valeur, None
        if not coups:
            if not jeu.obtenir_coups_valides(-joueur, plateau):
                valeur = self.evaluer(jeu, plateau, joueur)
            else:
                precedent, _ = self._negamax(jeu, plateau, profondeur - 1, -beta, -alpha, -joueur)
                valeur = -precedent
            self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, None)
            return valeur, None

        valeur = -INF
        meilleur_coup = None
        for coup in self._coups_ordonnes(coups, suggestion):
            suite = [ligne[:] for ligne in plateau]
            jeu.jouer_coup(*coup, joueur, suite)
            suivant, _ = self._negamax(jeu, suite, profondeur - 1, -beta, -alpha, -joueur)
            score = -suivant
            if score > valeur:
                valeur, meilleur_coup = score, coup
            alpha = max(alpha, valeur)
            if alpha >= beta:
                self.derniere_recherche.coupures += 1
                break
        self._enregistrer(cle, profondeur, valeur, alpha_initial, beta_initial, meilleur_coup)
        return valeur, meilleur_coup

    def obtenir_meilleur_coup(self, jeu: OthelloGame, joueur_ia: int) -> tuple[int, int] | None:
        """Retourne TOUJOURS un coup légal (ou None si passage obligatoire).

        Un score/coup n'est validé qu'après une itération entièrement terminée.
        L'algorithme et la table de transposition restent propres à cette IA.
        """
        debut = perf_counter()
        self.derniere_recherche = StatistiquesRecherche()
        coups = jeu.obtenir_coups_valides(joueur_ia)
        if not coups:
            self.derniere_recherche.temps = perf_counter() - debut
            self.noeuds_explores = 0
            return None
        meilleur_coup = self._coups_ordonnes(coups)[0]  # repli en cas de temps très court
        self._deadline = None if self.temps_max is None else debut + self.temps_max
        try:
            # 1 profondeur de l'énoncé = 2 demi-coups. Les itérations sont en demi-coups.
            for profondeur in range(1, self.profondeur_max * 2 + 1):
                if self.algorithme == "minimax":
                    score, coup = self._minimax(
                        jeu, jeu.plateau, profondeur, joueur_ia, joueur_ia)
                elif self.algorithme == "negamax":
                    score, coup = self._negamax(
                        jeu, jeu.plateau, profondeur, -INF, INF, joueur_ia)
                else:
                    score, coup = self._alphabeta(
                        jeu, jeu.plateau, profondeur, -INF, INF, joueur_ia, joueur_ia)
                if coup in coups:
                    meilleur_coup = coup
                    self.derniere_recherche.score = score
                    self.derniere_recherche.profondeur_atteinte = profondeur
        except TimeoutRecherche:
            self.derniere_recherche.timeout = True
        finally:
            self._deadline = None
            self.derniere_recherche.temps = perf_counter() - debut
            self.derniere_recherche.coup = meilleur_coup
            self.noeuds_explores = self.derniere_recherche.noeuds
        return meilleur_coup
