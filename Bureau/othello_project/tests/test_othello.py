"""Tests de règles, d'équivalence des recherches et de robustesse du time-out."""

import unittest

from ai import OthelloAI, SCORE_VICTOIRE
from benchmark import generer_ouverture, simuler_partie, tournoi, Configuration
from game import BLANC, NOIR, VIDE, OthelloGame


class TestRegles(unittest.TestCase):
    def test_initialisation_blanc_commence(self):
        jeu = OthelloGame()
        self.assertEqual(jeu.joueur_actif, BLANC)
        self.assertEqual(jeu.calculer_score(), (2, 2))
        self.assertEqual(set(jeu.obtenir_coups_valides(BLANC)),
                         {(2, 4), (3, 5), (4, 2), (5, 3)})
        self.assertEqual(jeu.nombre_coups_joues(), 0)

    def test_retournement_score_et_copie(self):
        jeu = OthelloGame()
        copie = jeu.copier()
        self.assertTrue(jeu.jouer_coup(2, 4, BLANC))
        self.assertEqual(jeu.plateau[3][4], BLANC)
        self.assertEqual(jeu.calculer_score(), (1, 4))
        self.assertEqual(jeu.nombre_coups_joues(), 1)
        self.assertEqual(copie.calculer_score(), (2, 2))

    def test_coups_illegaux_et_limites(self):
        jeu = OthelloGame()
        self.assertFalse(jeu.jouer_coup(-1, 4, BLANC))
        self.assertFalse(jeu.jouer_coup(8, 8, BLANC))
        self.assertFalse(jeu.jouer_coup(3, 3, BLANC))
        self.assertFalse(jeu.jouer_coup(0, 0, BLANC))
        self.assertEqual(jeu.calculer_score(), (2, 2))

    def test_passage_de_tour(self):
        jeu = OthelloGame()
        jeu.plateau = [[VIDE] * 8 for _ in range(8)]
        jeu.plateau[0][0] = NOIR
        jeu.plateau[0][1] = BLANC
        jeu.joueur_actif = BLANC
        self.assertEqual(jeu.obtenir_coups_valides(BLANC), [])
        self.assertEqual(jeu.obtenir_coups_valides(NOIR), [(0, 2)])
        self.assertTrue(jeu.passer_si_necessaire())
        self.assertEqual(jeu.joueur_actif, NOIR)
        self.assertTrue(jeu.jouer_coup(0, 2, NOIR))
        self.assertTrue(jeu.est_termine())
        self.assertFalse(jeu.passer_si_necessaire())

    def test_terminale(self):
        jeu = OthelloGame()
        jeu.plateau = [[NOIR] * 8 for _ in range(8)]
        self.assertTrue(jeu.est_termine())
        self.assertEqual(jeu.calculer_score(), (64, 0))


class TestIA(unittest.TestCase):
    def test_quatre_strategies_et_coins(self):
        jeu = OthelloGame()
        plateau = jeu.copier().plateau
        plateau[0][0] = BLANC
        mob = OthelloAI("mobilite")
        self.assertGreater(mob.eval_mobilite(jeu, plateau, BLANC),
                           -mob.eval_mobilite(jeu, plateau, BLANC))
        for strategie in ("absolu", "positionnel", "mobilite", "mixte"):
            ia = OthelloAI(strategie)
            self.assertIsInstance(ia.evaluer(jeu, plateau, BLANC), float)

    def test_victoire_terminale_prioritaire(self):
        jeu = OthelloGame()
        jeu.plateau = [[BLANC] * 8 for _ in range(8)]
        for strategie in ("absolu", "positionnel", "mobilite", "mixte"):
            ia = OthelloAI(strategie)
            self.assertGreater(ia.evaluer(jeu, jeu.plateau, BLANC), SCORE_VICTOIRE)
            self.assertLess(ia.evaluer(jeu, jeu.plateau, NOIR), -SCORE_VICTOIRE)

    def test_equivalence_sans_cache(self):
        jeu = generer_ouverture(123, 4)
        joueur = jeu.joueur_actif
        resultats = []
        for algo in ("minimax", "alphabeta", "negamax"):
            ia = OthelloAI("mixte", profondeur_max=1, algorithme=algo,
                           temps_max=None, table_transposition=False, tri_coups=False)
            coup = ia.obtenir_meilleur_coup(jeu, joueur)
            self.assertIn(coup, jeu.obtenir_coups_valides(joueur))
            self.assertEqual(ia.derniere_recherche.profondeur_atteinte, 2)
            resultats.append((coup, ia.derniere_recherche.score))
        self.assertEqual(resultats[0], resultats[1])
        self.assertEqual(resultats[0], resultats[2])

    def test_cache_conserve_et_equivalent(self):
        jeu = generer_ouverture(40, 5)
        joueur = jeu.joueur_actif
        with_tt = OthelloAI("positionnel", 1, "alphabeta", None, True, True)
        without_tt = OthelloAI("positionnel", 1, "alphabeta", None, False, True)
        coup = with_tt.obtenir_meilleur_coup(jeu, joueur)
        valeur = with_tt.derniere_recherche.score
        coup_reference = without_tt.obtenir_meilleur_coup(jeu, joueur)
        self.assertEqual((coup, valeur), (coup_reference, without_tt.derniere_recherche.score))
        self.assertTrue(with_tt.table_transposition)
        with_tt.obtenir_meilleur_coup(jeu, joueur)
        self.assertGreater(with_tt.derniere_recherche.tt_hits, 0)
        self.assertIsNot(with_tt.table_transposition, without_tt.table_transposition)

    def test_timeout_repli_legal(self):
        jeu = OthelloGame()
        ia = OthelloAI(profondeur_max=5, temps_max=1e-12)
        coup = ia.obtenir_meilleur_coup(jeu, BLANC)
        self.assertIn(coup, jeu.obtenir_coups_valides(BLANC))
        self.assertTrue(ia.derniere_recherche.timeout)
        self.assertEqual(ia.derniere_recherche.profondeur_atteinte, 0)

    def test_aucun_coup_possible(self):
        jeu = OthelloGame()
        jeu.plateau = [[VIDE] * 8 for _ in range(8)]
        jeu.plateau[0][0] = NOIR
        jeu.plateau[0][1] = BLANC
        ia = OthelloAI(temps_max=None)
        self.assertIsNone(ia.obtenir_meilleur_coup(jeu, BLANC))

    def test_minimax_plus_de_noeuds_que_ab(self):
        jeu = generer_ouverture(42, 4)
        mi = OthelloAI("mixte", 1, "minimax", None, False, False)
        ab = OthelloAI("mixte", 1, "alphabeta", None, False, False)
        mi.obtenir_meilleur_coup(jeu, jeu.joueur_actif)
        ab.obtenir_meilleur_coup(jeu, jeu.joueur_actif)
        self.assertLessEqual(ab.noeuds_explores, mi.noeuds_explores)


class TestBenchmarks(unittest.TestCase):
    def test_ouvertures_reproductibles(self):
        self.assertEqual(generer_ouverture(23).plateau, generer_ouverture(23).plateau)
        self.assertNotEqual(generer_ouverture(23).plateau, generer_ouverture(24).plateau)

    def test_partie_complete_ia_contre_ia(self):
        a = OthelloAI("absolu", 1, temps_max=0.01)
        b = OthelloAI("positionnel", 1, temps_max=0.01)
        vainqueur, noir, blanc, stats = simuler_partie(a, b)
        self.assertIn(vainqueur, (NOIR, BLANC, 0))
        self.assertLessEqual(noir + blanc, 64)
        self.assertGreater(stats[NOIR]["coups"], 0)
        self.assertGreater(stats[BLANC]["coups"], 0)

    def test_tournoi_equilibre(self):
        a = Configuration("A", "absolu", 1)
        b = Configuration("B", "positionnel", 1)
        resultat = tournoi(a, b, 2, temps_max=0.01, afficher=False)
        total = (resultat["totaux"][0]["victoires"]
                 + resultat["totaux"][1]["victoires"] + resultat["egalites"])
        self.assertEqual(total, 2)
        with self.assertRaises(ValueError):
            tournoi(a, b, 3, afficher=False)


if __name__ == "__main__":
    unittest.main()
