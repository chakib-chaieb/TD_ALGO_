# -*- coding: utf-8 -*-
"""
Ordonnancement de la maintenance de centrales électriques par Algorithme Génétique
- Encodage : 7 gènes de 4 bits (1 gène = 1 unité, 1 bit = 1 intervalle)
- Fitness  : plus petite réserve nette sur les 4 intervalles (0 si négative)
- Sélection: loterie (roulette proportionnelle à la fitness)
- Croisement: 1 point, uniquement aux frontières de gènes
- Mutation : inversion (3 variantes au choix)
"""
import random

# ---------------------------------------------------------------- DONNEES
CAPACITES = [20, 15, 35, 40, 15, 15, 10]     # MW par unité
DEMANDES = [80, 90, 65, 70]                  # MW par intervalle
CAP_TOTALE = sum(CAPACITES)                  # 150 MW
N_UNITES = len(CAPACITES)
N_INTERV = len(DEMANDES)

# Maintenance possible par unité (blocs contigus de 4 bits)
PATTERNS_2 = ["1100", "0110", "0011"]                  # unités 1 et 2 (2 intervalles)
PATTERNS_1 = ["1000", "0100", "0010", "0001"]          # unités 3 à 7 (1 intervalle)
POSSIBLES = [PATTERNS_2, PATTERNS_2] + [PATTERNS_1] * 5

# ---------------------------------------------------------------- PARAMETRES
TAILLE_POP = 50          # ~ 6 à 7 fois le nombre de variables (7)
N_GENERATIONS = 100
P_CROISEMENT = 0.8
P_MUTATION = 0.1
ELITISME = True
TYPE_MUTATION = "inversion_segment"   # "inversion_segment" | "inversion_bits" | "remplacement"


# ---------------------------------------------------------------- CHROMOSOME
def creer_chromosome():
    """Un chromosome = liste de 7 chaînes de 4 bits (toujours valides)."""
    return [random.choice(POSSIBLES[u]) for u in range(N_UNITES)]


def afficher(chromo):
    return " ".join(chromo)


# ---------------------------------------------------------------- FONCTION OBJECTIVE
def reserves(chromo):
    """Réserve nette pour chaque intervalle = capacité totale - puissance en maintenance - demande."""
    res = []
    for i in range(N_INTERV):
        p_perdue = sum(CAPACITES[u] for u in range(N_UNITES) if chromo[u][i] == "1")
        res.append(CAP_TOTALE - p_perdue - DEMANDES[i])
    return res


def fitness(chromo):
    """Performance = plus petite réserve (0 si négative)."""
    return max(0, min(reserves(chromo)))


# ---------------------------------------------------------------- SELECTION PAR LOTERIE
def selection_loterie(population, fits):
    """Roulette : probabilité de choix proportionnelle à la fitness."""
    total = sum(fits)
    if total == 0:                         # tous nuls -> tirage uniforme
        return random.choice(population)
    tirage = random.uniform(0, total)
    cumul = 0
    for chromo, f in zip(population, fits):
        cumul += f
        if cumul >= tirage:
            return chromo
    return population[-1]


# ---------------------------------------------------------------- CROISEMENT
def croisement(p1, p2):
    """Croisement à 1 point, coupure uniquement entre deux gènes de 4 bits."""
    if random.random() > P_CROISEMENT:
        return p1[:], p2[:]
    pt = random.randint(1, N_UNITES - 1)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]


# ---------------------------------------------------------------- MUTATIONS
def mutation_inversion_segment(chromo):
    """Inversion : on choisit 2 positions de gènes et on inverse l'ordre du segment.
    NB : un gène de l'unité 1/2 (2 intervalles) pouvant migrer vers l'unité 3-7,
    on répare ensuite pour respecter les motifs autorisés de chaque unité."""
    c = chromo[:]
    i, j = sorted(random.sample(range(N_UNITES), 2))
    c[i:j + 1] = reversed(c[i:j + 1])
    return reparer(c)


def mutation_inversion_bits(chromo):
    """Inversion des bits d'un gène (1100 -> 0011, 1000 -> 0001...). Toujours valide."""
    c = chromo[:]
    u = random.randrange(N_UNITES)
    c[u] = c[u][::-1]
    return c


def mutation_remplacement(chromo):
    """Remplace un gène par un autre motif valide de la même unité."""
    c = chromo[:]
    u = random.randrange(N_UNITES)
    c[u] = random.choice(POSSIBLES[u])
    return c


def reparer(chromo):
    """Si un gène n'est pas autorisé pour son unité, on le remplace par un motif valide
    (même nombre de bits à 1 que requis)."""
    for u in range(N_UNITES):
        if chromo[u] not in POSSIBLES[u]:
            chromo[u] = random.choice(POSSIBLES[u])
    return chromo


MUTATIONS = {
    "inversion_segment": mutation_inversion_segment,
    "inversion_bits": mutation_inversion_bits,
    "remplacement": mutation_remplacement,
}


def mutation(chromo):
    if random.random() < P_MUTATION:
        return MUTATIONS[TYPE_MUTATION](chromo)
    return chromo


# ---------------------------------------------------------------- BOUCLE PRINCIPALE
def algorithme_genetique(verbose=True):
    population = [creer_chromosome() for _ in range(TAILLE_POP)]
    meilleur, meilleur_f = None, -1
    historique = []

    for gen in range(N_GENERATIONS):
        fits = [fitness(c) for c in population]

        # meilleur de la génération
        idx = max(range(TAILLE_POP), key=lambda k: fits[k])
        if fits[idx] > meilleur_f:
            meilleur, meilleur_f = population[idx][:], fits[idx]
        historique.append(meilleur_f)

        if verbose and gen % 10 == 0:
            print(f"Génération {gen:3d} | meilleur = {meilleur_f:3d} MW | moyenne = {sum(fits)/TAILLE_POP:.1f}")

        # nouvelle population
        nouvelle = [meilleur[:]] if ELITISME else []
        while len(nouvelle) < TAILLE_POP:
            p1 = selection_loterie(population, fits)
            p2 = selection_loterie(population, fits)
            e1, e2 = croisement(p1, p2)
            nouvelle.append(mutation(e1))
            if len(nouvelle) < TAILLE_POP:
                nouvelle.append(mutation(e2))
        population = nouvelle

    return meilleur, meilleur_f, historique


if __name__ == "__main__":
    random.seed()
    # Vérification sur l'exemple du cours : performance attendue = 20
    exemple = ["0110", "0011", "0001", "1000", "0100", "0010", "1000"]
    print("Exemple du cours :", afficher(exemple), "-> réserves", reserves(exemple), "-> performance", fitness(exemple))
    print()

    for t in MUTATIONS:
        TYPE_MUTATION = t
        print(f"===== Mutation : {t} =====")
        sol, f, _ = algorithme_genetique(verbose=False)
        print("Meilleure cédule :", afficher(sol))
        print("Réserves par intervalle :", reserves(sol), "| performance =", f, "MW")
        for u in range(N_UNITES):
            ints = [i + 1 for i in range(N_INTERV) if sol[u][i] == "1"]
            print(f"  Unité {u+1} ({CAPACITES[u]} MW) -> intervalle(s) {ints}")
        print()
