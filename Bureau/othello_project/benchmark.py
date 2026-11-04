"""Tournois reproductibles et ablations pour le rapport de TP.

Exemples :
    python benchmark.py --scenario algorithmes --parties 4 --profondeur 2
    python benchmark.py --scenario strategies --parties 4 --sortie resultats.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from ai import OthelloAI
from game import BLANC, NOIR, OthelloGame


@dataclass(frozen=True)
class Configuration:
    nom: str
    strategie: str = "mixte"
    profondeur: int = 2
    algorithme: str = "alphabeta"
    tt: bool = True
    tri: bool = True


def generer_ouverture(graine: int, coups_a_jouer: int = 6) -> OthelloGame:
    """Prépare une ouverture légale, identique pour les deux manches d'une paire."""
    alea = random.Random(graine)
    jeu = OthelloGame()
    for _ in range(coups_a_jouer):
        if jeu.est_termine():
            break
        jeu.passer_si_necessaire()
        coups = jeu.obtenir_coups_valides(jeu.joueur_actif)
        if not coups:
            break
        coup = alea.choice(coups)
        assert jeu.jouer_coup(*coup, jeu.joueur_actif)
        jeu.changer_joueur()
    return jeu


def simuler_partie(
    ai_noir: OthelloAI, ai_blanc: OthelloAI,
    partie_initiale: OthelloGame | None = None,
) -> tuple[int, int, int, dict[int, dict[str, float]]]:
    """Simule une partie sans Pygame ; statistiques séparées pour chaque IA."""
    if ai_noir is ai_blanc:
        raise ValueError("Chaque IA doit disposer de sa propre instance et de son propre cache.")
    jeu = partie_initiale.copier() if partie_initiale is not None else OthelloGame()
    stats = {
        NOIR: {"temps": 0.0, "noeuds": 0, "coups": 0, "coupures": 0,
               "tt_hits": 0, "tt_stores": 0, "profondeur_cumulee": 0, "timeouts": 0},
        BLANC: {"temps": 0.0, "noeuds": 0, "coups": 0, "coupures": 0,
                "tt_hits": 0, "tt_stores": 0, "profondeur_cumulee": 0, "timeouts": 0},
    }
    while not jeu.est_termine():
        joueur = jeu.joueur_actif
        if jeu.passer_si_necessaire():
            continue
        ia = ai_noir if joueur == NOIR else ai_blanc
        coup = ia.obtenir_meilleur_coup(jeu, joueur)
        mesure = ia.derniere_recherche
        stats[joueur]["temps"] += mesure.temps
        stats[joueur]["noeuds"] += mesure.noeuds
        stats[joueur]["coupures"] += mesure.coupures
        stats[joueur]["tt_hits"] += mesure.tt_hits
        stats[joueur]["tt_stores"] += mesure.tt_stores
        stats[joueur]["profondeur_cumulee"] += mesure.profondeur_atteinte
        stats[joueur]["timeouts"] += int(mesure.timeout)
        stats[joueur]["coups"] += 1
        if coup is None or not jeu.jouer_coup(*coup, joueur):
            raise RuntimeError(f"L'IA a renvoyé un coup illégal : {coup}")
        jeu.changer_joueur()

    score_noir, score_blanc = jeu.calculer_score()
    vainqueur = NOIR if score_noir > score_blanc else BLANC if score_blanc > score_noir else 0
    return vainqueur, score_noir, score_blanc, stats


def executer_tournoi(
    strategie_1: str, prof_1: int, strategie_2: str, prof_2: int,
    nombre_parties: int = 6, *,
    algo_1: str = "alphabeta", algo_2: str = "alphabeta",
    tt_1: bool = True, tt_2: bool = True,
    tri_1: bool = True, tri_2: bool = True,
    temps_max: float | None = 0.35, graine: int = 42,
) -> dict:
    """API compatible avec le prototype : alterne les couleurs à ouverture identique."""
    c1 = Configuration("Joueur 1", strategie_1, prof_1, algo_1, tt_1, tri_1)
    c2 = Configuration("Joueur 2", strategie_2, prof_2, algo_2, tt_2, tri_2)
    return tournoi(c1, c2, nombre_parties, temps_max=temps_max, graine=graine)


def tournoi(
    a: Configuration, b: Configuration, nombre_parties: int = 4, *,
    temps_max: float | None = 0.35, graine: int = 42,
    afficher: bool = True,
) -> dict:
    if nombre_parties < 2 or nombre_parties % 2:
        raise ValueError("Le nombre de parties doit être pair et >= 2.")
    totaux = [dict(victoires=0, temps=0.0, noeuds=0, coups=0, coupures=0,
                   tt_hits=0, tt_stores=0, profondeur_cumulee=0, timeouts=0)
              for _ in range(2)]
    egalites = 0

    for paire in range(nombre_parties // 2):
        ouverture = generer_ouverture(graine + paire, coups_a_jouer=4 + 2 * (paire % 4))
        for manche in range(2):
            conf_noir, conf_blanc = (a, b) if manche == 0 else (b, a)
            ia_noir = OthelloAI(conf_noir.strategie, conf_noir.profondeur,
                                conf_noir.algorithme, temps_max, conf_noir.tt, conf_noir.tri)
            ia_blanc = OthelloAI(conf_blanc.strategie, conf_blanc.profondeur,
                                 conf_blanc.algorithme, temps_max, conf_blanc.tt, conf_blanc.tri)
            vainqueur, _, _, stats = simuler_partie(ia_noir, ia_blanc, ouverture)
            couleurs = (NOIR, BLANC) if manche == 0 else (BLANC, NOIR)
            for indice, couleur in enumerate(couleurs):
                for cle in stats[couleur]:
                    totaux[indice][cle] += stats[couleur][cle]
                if vainqueur == couleur:
                    totaux[indice]["victoires"] += 1
            if vainqueur == 0:
                egalites += 1

    resultat = {
        "config_a": a, "config_b": b, "parties": nombre_parties,
        "egalites": egalites, "totaux": totaux, "temps_max": temps_max,
        "graine": graine,
    }
    if afficher:
        print(f"\n{a.nom}  VS  {b.nom} — {nombre_parties} parties (graine={graine})")
        for cfg, tot in zip((a, b), totaux):
            n = max(1, tot["coups"])
            print(f"  {cfg.nom:26s} {tot['victoires']} victoires | "
                  f"{tot['temps']/n:.4f} s/coup | {tot['noeuds']/n:.0f} nœuds/coup | "
                  f"{tot['profondeur_cumulee']/n:.2f} demi-coups atteints | "
                  f"TT hits {tot['tt_hits']} | timeouts {tot['timeouts']}")
        print(f"  Égalités : {egalites}")
    return resultat


def configurations(scenario: str, profondeur: int) -> list[tuple[Configuration, Configuration]]:
    base = Configuration("Alpha-Bêta", profondeur=profondeur)
    minimax = Configuration("Min-Max", profondeur=profondeur, algorithme="minimax", tt=False, tri=False)
    ab_pur = Configuration("Alpha-Bêta sans aide", profondeur=profondeur, tt=False, tri=False)
    negamax = Configuration("NegaMax", profondeur=profondeur, algorithme="negamax", tt=False, tri=False)
    sans_tt = Configuration("Sans transpositions", profondeur=profondeur, tt=False)
    sans_tri = Configuration("Sans ordonnancement", profondeur=profondeur, tri=False)
    strategies = [Configuration(s, strategie=s, profondeur=profondeur)
                  for s in ("absolu", "positionnel", "mobilite", "mixte")]
    comparaisons = {
        "algorithmes": [(minimax, ab_pur), (ab_pur, negamax)],
        "optimisations": [(base, sans_tt), (base, sans_tri)],
        "strategies": list(combinations(strategies, 2)),
        "profondeur": [(Configuration(f"P{max(1, profondeur-1)}", profondeur=max(1, profondeur-1)),
                         Configuration(f"P{max(2, profondeur)}", profondeur=max(2, profondeur)))],
    }
    if scenario == "tous":
        return sum(comparaisons.values(), [])
    return comparaisons[scenario]


def exporter_csv(resultats: list[dict], sortie: str) -> None:
    colonnes = ["confrontation", "configuration", "strategie", "algorithme", "profondeur_cible",
                "cache", "ordonnancement", "parties", "victoires", "egalites", "temps_max_s",
                "temps_moyen_coup_s", "noeuds_moyens_coup", "profondeur_moyenne_demi_coups",
                "coupures", "tt_hits", "tt_stores", "timeouts", "graine"]
    chemin = Path(sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=colonnes)
        writer.writeheader()
        for index, resultat in enumerate(resultats, start=1):
            for cfg, tot in zip((resultat["config_a"], resultat["config_b"]), resultat["totaux"]):
                n = max(1, tot["coups"])
                writer.writerow({
                    "confrontation": index, "configuration": cfg.nom,
                    "strategie": cfg.strategie, "algorithme": cfg.algorithme,
                    "profondeur_cible": cfg.profondeur, "cache": cfg.tt,
                    "ordonnancement": cfg.tri, "parties": resultat["parties"],
                    "victoires": tot["victoires"], "egalites": resultat["egalites"],
                    "temps_max_s": resultat["temps_max"],
                    "temps_moyen_coup_s": round(tot["temps"] / n, 6),
                    "noeuds_moyens_coup": round(tot["noeuds"] / n, 2),
                    "profondeur_moyenne_demi_coups": round(tot["profondeur_cumulee"] / n, 2),
                    "coupures": tot["coupures"], "tt_hits": tot["tt_hits"],
                    "tt_stores": tot["tt_stores"], "timeouts": tot["timeouts"],
                    "graine": resultat["graine"],
                })
    print(f"\nRésultats exportés : {chemin}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmarks IA Othello, à ouvertures et couleurs équilibrées")
    parser.add_argument("--scenario", choices=("tous", "algorithmes", "optimisations", "strategies", "profondeur"),
                        default="tous")
    parser.add_argument("--parties", type=int, default=2, help="Nombre pair de parties par confrontation")
    parser.add_argument("--profondeur", type=int, default=2, help="P=1 représente deux demi-coups")
    parser.add_argument("--temps", type=float, default=0.35, help="Limite par coup (secondes)")
    parser.add_argument("--graine", type=int, default=42)
    parser.add_argument("--sortie", default="resultats.csv")
    args = parser.parse_args()
    resultats = [tournoi(a, b, args.parties, temps_max=args.temps, graine=args.graine)
                 for a, b in configurations(args.scenario, args.profondeur)]
    exporter_csv(resultats, args.sortie)


if __name__ == "__main__":
    main()
