# Requirements — Onglet Scout (Fenêtre de réception)

## Contexte
Même moteur « fenêtre de réception » que les autres onglets
(= séparation receveur ciblé ↔ défenseur le plus proche).
Ce document couvre **uniquement l'onglet Scout** (persona : évaluation / recrutement).

**Question directrice du Scout :**
> « Quels défenseurs referment la fenêtre plus vite qu'un défenseur moyen
> parti de la même position ? »

**Principe :** le scout **compare des joueurs entre eux** → on utilise un **indice normalisé**
(fermeture réelle vs attendue, « parti de la même position »), mais exprimé en **unités concrètes** :
placement en **yd**, vitesse de fermeture en **yd/s**.

---

## User stories (format EARS)

### US-S1 — Classement des défenseurs
**En tant que** scout,
**je veux** un classement des défenseurs par indice de fermeture,
**afin d'** identifier ceux qui referment la fenêtre mieux qu'un défenseur moyen.

- WHEN l'onglet Scout est ouvert, THE SYSTEM SHALL afficher un tableau de défenseurs
  trié par `closing_index` décroissant.
- THE SYSTEM SHALL afficher par ligne : rang, nom, poste, `n_plays`,
  `placement` (yd), `closing_index` (yd/s) et son intervalle de confiance `ci`.

### US-S2 — Fiche joueur (placement vs rattrapage)
**En tant que** scout,
**je veux** une fiche séparant le **placement au lancer** et le **rattrapage pendant le vol**,
**afin de** distinguer un défenseur bien placé d'un défenseur qui referme vite.

- WHEN le scout clique un défenseur, THE SYSTEM SHALL ouvrir une fiche à deux volets :
  - **Placement au lancer** : distance moyenne au receveur au lancer (`placement`, yd).
  - **Rattrapage pendant le vol** : `closing_rate` (yd/s) vs `expected_rate` (yd/s)
    → `closing_index` = écart (yd/s), avec `ci`.
- THE SYSTEM SHALL afficher une phrase de synthèse factuelle
  (« referme 0,42 yd/s plus vite que la moyenne, pour un placement de 5,2 yd »).

### US-S3 — Fiabilité de l'échantillon
**En tant que** scout,
**je veux** ne classer que les joueurs ayant assez d'actions,
**afin de** ne comparer que des évaluations solides.

- IF un défenseur a `n_plays < 20`, THEN THE SYSTEM SHALL l'exclure du classement
  (ou le marquer « non classé »).

### US-S4 — Transparence du biais de sélection
**En tant que** scout,
**je veux** savoir que le classement ne porte que sur les actions où le défenseur était exposé,
**afin de** interpréter correctement les résultats.

- THE SYSTEM SHALL afficher clairement : « classement parmi les défenseurs exposés au ballon,
  pas toute la ligue ».

---

## Hors périmètre
- Agrégation par situation (couverture/route) → onglet Coach.
- Animation d'une action → onglet Broadcast.

## Limites / biais à afficher
- Seuil `n_plays ≥ 20`.
- Biais de sélection : seuls les défenseurs **les plus proches du receveur ciblé** sont suivis.
- Indice réutilisable sur n'importe quelle saison au même format.
