# Othello — TP Fondements de l'IA

Implémentation Python d'Othello (8 × 8), d'IA pour les jeux à deux joueurs, de tournois reproductibles et d'une interface facultative Pygame.

## Installation

Python **3.10 ou plus récent**. Les règles, les IA et les benchmarks ne nécessitent aucune dépendance externe.

```bash
python -m pip install -r requirements.txt  # uniquement pour l'interface Pygame
```

## Jouer

```bash
python main.py                                      # humain blanc vs IA noire
python main.py --humain noir --profondeur 2 --temps 1.0
python main.py --mode ia-ia --strategie-blanc mobilite --strategie-noir mixte
python main.py --help
```

Le sujet du TP impose de **faire commencer les blancs**, même si la convention usuelle d'Othello fait commencer les noirs. Le joueur humain peut choisir sa couleur. L'IA joue seule lorsqu'elle est active ; les points rouges indiquent les coups autorisés au joueur humain.

## Algorithmes et stratégies

- `minimax` : version de référence exhaustive jusqu'à une profondeur fixée, sans élagage ni transpositions ;
- `alphabeta` : Min-Max avec coupures Alpha-Bêta ;
- `negamax` : formulation symétrique avec coupures Alpha-Bêta ;
- table de transposition : mémorisation de l'état du plateau, du joueur courant, de la profondeur, du score et du type de borne (`EXACT`, `INFERIEUR`, `SUPERIEUR`), conservée **entre les tours d'une même IA** ;
- ordre des coups : proposition du cache puis préférence aux coins / poids statiques ;
- approfondissement itératif : coup le plus fort de la **dernière itération intégralement achevée** ; si le temps est écoulé avant la première itération, repli sur un coup autorisé.

Stratégies d'évaluation disponibles : `absolu`, `positionnel`, `mobilite`, `mixte`. La mobilité inclut un bonus pour les **coins possédés**. En stratégie mixte, les **25 premiers coups** utilisent le positionnel ; le milieu de partie utilise la mobilité ; les **16 dernières cases libres** utilisent le nombre de pions. Ces seuils et pondérations doivent être explicités dans le rapport.

**Convention de profondeur du TP** : une profondeur annoncée de `1` correspond aux coups du joueur **et** à la réponse adverse, soit **2 demi-coups** (`plies`). Ainsi, `--profondeur 2` recherche jusqu'à 4 demi-coups. Les statistiques `profondeur_atteinte` sont exprimées **en demi-coups**.

**Attention aux contraintes temporelles :** le budget `--temps` est en secondes **par décision**, et peut conduire à une profondeur effectivement inférieure à la cible. Les statistiques de temps prennent en compte toutes les itérations (y compris une itération interrompue). La version de référence Min-Max est également interrompue si son temps est écoulé.

## Benchmarks, sans interface

```bash
python benchmark.py --scenario tous --parties 2 --profondeur 2 --temps 0.35 --sortie resultats.csv
python benchmark.py --scenario algorithmes --parties 4 --profondeur 2 --temps 0.5
python benchmark.py --scenario strategies --parties 6 --profondeur 2 --temps 1.0
python benchmark.py --scenario optimisations --parties 4 --profondeur 2
python benchmark.py --scenario profondeur --parties 4 --profondeur 3
```

Scénarios :

1. `algorithmes` : **Min-Max vs Alpha-Bêta** (cache et ordonnancement désactivés), puis **Alpha-Bêta vs NegaMax** ;
2. `optimisations` : impact du cache et de l'ordonnancement, chacun isolé ;
3. `strategies` : six oppositions de `absolu`, `positionnel`, `mobilite`, `mixte` ;
4. `profondeur` : niveau P-1 contre niveau P ;
5. `tous` : ensemble des précédents.

Pour chaque confrontation, le nombre de parties est **pair** : une même ouverture est jouée une fois dans chaque attribution des couleurs. Les ouvertures sont générées légalement avec une **graine fixe** (`--graine`) et changent à chaque paire, pour limiter le biais du premier joueur. Le CSV contient les victoires, égalités, temps moyen/coup, nœuds moyens/coup, profondeur réelle moyenne, coupures, hits dans le cache, écritures et interruptions par timeout. Les caches des IA concurrentes ne sont **jamais partagés**.

Pour mesurer le gain brut d'Alpha-Bêta contre Min-Max sans biais de timeout, utiliser une faible profondeur et **augmenter le budget temporel** jusqu'à ce que les deux configurations atteignent systématiquement la profondeur demandée. Lorsque ce n'est pas le cas, comparer les performances sous **budget temps égal**, mais ne pas attribuer les différences de nœuds au seul élagage.

## Tests

```bash
python -m unittest discover -s tests -v
```

Les tests couvrent : règles initiales (blanc en premier), captures, invalidité, passages de tour, fin de partie, équivalence des trois algorithmes sur une même position, cache, interruption de recherche, parties IA–IA et tournois.

## Architecture

| Fichier | Responsabilité |
| --- | --- |
| `game.py` | Plateau, légalité, captures, tours, fin de partie |
| `ai.py` | Stratégies, Min-Max, Alpha-Bêta, NegaMax, time-out, cache, statistiques |
| `main.py` | Pygame : humain–IA ou IA–IA |
| `benchmark.py` | Tournois, équilibrage des couleurs, CSV |
| `tests/test_othello.py` | Tests automatisés |

Le rapport académique (introduction, analyse, validation, discussion, conclusion, figures et bibliographie) est à produire séparément. Le code pourra être ajouté en annexe comme le demande l'énoncé.
