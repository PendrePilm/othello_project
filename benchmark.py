import time
from game import BLANC, NOIR, OthelloGame
from ai import OthelloAI

def simuler_partie(ai_noir, ai_blanc):
    """
    Simule une partie complète entre deux IA sans affichage graphique.
    Retourne le vainqueur, les scores, le nombre total de coups, 
    le temps total de réflexion et le nombre de nœuds explorés par chaque IA.
    """
    jeu = OthelloGame()
    
    stats = {
        NOIR: {"temps": 0.0, "noeuds": 0, "coups": 0},
        BLANC: {"temps": 0.0, "noeuds": 0, "coups": 0}
    }

    while not jeu.est_termine():
        joueur = jeu.joueur_actif
        ia_courante = ai_noir if joueur == NOIR else ai_blanc
        
        coups_valides = jeu.obtenir_coups_valides(joueur)
        if coups_valides:
            t0 = time.time()
            coup = ia_courante.obtenir_meilleur_coup(jeu, joueur)
            t1 = time.time()
            
            stats[joueur]["temps"] += (t1 - t0)
            stats[joueur]["noeuds"] += ia_courante.noeuds_explores
            stats[joueur]["coups"] += 1
            
            if coup:
                jeu.jouer_coup(coup[0], coup[1], joueur)
                
        jeu.changer_joueur()

    score_noir, score_blanc = jeu.calculer_score()
    if score_noir > score_blanc:
        vainqueur = NOIR
    elif score_blanc > score_noir:
        vainqueur = BLANC
    else:
        vainqueur = 0  # Égalité

    return vainqueur, score_noir, score_blanc, stats

def executer_tournoi(strategie_1, prof_1, strategie_2, prof_2, nombre_parties=10):
    """
    Organise plusieurs parties entre deux configurations en alternant les couleurs.
    """
    print(f"\n--- MATCH : {strategie_1.upper()} (Prof. {prof_1}) VS {strategie_2.upper()} (Prof. {prof_2}) ---")
    
    victoires_1 = 0
    victoires_2 = 0
    egalites = 0
    
    total_temps_1, total_noeuds_1, total_coups_1 = 0, 0, 0
    total_temps_2, total_noeuds_2, total_coups_2 = 0, 0, 0

    for i in range(nombre_parties):
        # Alternance des couleurs à chaque partie pour garantir l'équité
        if i % 2 == 0:
            ai_noir = OthelloAI(strategie=strategie_1, profondeur_max=prof_1)
            ai_blanc = OthelloAI(strategie=strategie_2, profondeur_max=prof_2)
            p1_couleur, p2_couleur = NOIR, BLANC
        else:
            ai_noir = OthelloAI(strategie=strategie_2, profondeur_max=prof_2)
            ai_blanc = OthelloAI(strategie=strategie_1, profondeur_max=prof_1)
            p1_couleur, p2_couleur = BLANC, NOIR

        vainqueur, s_noir, s_blanc, stats = simuler_partie(ai_noir, ai_blanc)

        # Cumul des statistiques pour le Joueur 1
        total_temps_1 += stats[p1_couleur]["temps"]
        total_noeuds_1 += stats[p1_couleur]["noeuds"]
        total_coups_1 += stats[p1_couleur]["coups"]

        # Cumul des statistiques pour le Joueur 2
        total_temps_2 += stats[p2_couleur]["temps"]
        total_noeuds_2 += stats[p2_couleur]["noeuds"]
        total_coups_2 += stats[p2_couleur]["coups"]

        if vainqueur == p1_couleur:
            victoires_1 += 1
        elif vainqueur == p2_couleur:
            victoires_2 += 1
        else:
            egalites += 1

    # Affichage des résultats synthétiques
    t_moyen_1 = (total_temps_1 / total_coups_1) if total_coups_1 > 0 else 0
    noeuds_moyen_1 = (total_noeuds_1 / total_coups_1) if total_coups_1 > 0 else 0
    
    t_moyen_2 = (total_temps_2 / total_coups_2) if total_coups_2 > 0 else 0
    noeuds_moyen_2 = (total_noeuds_2 / total_coups_2) if total_coups_2 > 0 else 0

    print(f"Résultats sur {nombre_parties} parties :")
    print(f" - {strategie_1} (P{prof_1}) : {victoires_1} victoires | Temps moy/coup: {t_moyen_1:.4f}s | Nœuds moy/coup: {noeuds_moyen_1:.0f}")
    print(f" - {strategie_2} (P{prof_2}) : {victoires_2} victoires | Temps moy/coup: {t_moyen_2:.4f}s | Nœuds moy/coup: {noeuds_moyen_2:.0f}")
    print(f" - Égalités : {egalites}")

if __name__ == "__main__":
    # Test 1 : Stratégie Absolue contre Stratégie Positionnelle à profondeur égale
    executer_tournoi("absolu", 3, "positionnel", 3, nombre_parties=6)
    
    # Test 2 : Stratégie Positionnelle contre Stratégie Mixte à profondeur égale
    executer_tournoi("positionnel", 3, "mixte", 3, nombre_parties=6)

    # Test 3 : Impact de la profondeur de recherche (Profondeur 2 vs Profondeur 4)
    executer_tournoi("mixte", 2, "mixte", 4, nombre_parties=4)