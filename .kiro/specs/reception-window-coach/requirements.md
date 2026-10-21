# Requirements — Onglet Coach (Fenêtre de réception)

## Contexte
Application d'analyse NFL Big Data Bowl 2026. Moteur unique « fenêtre de réception »
(= séparation entre le receveur ciblé et le défenseur le plus proche), décliné en 3 onglets.
Ce document couvre **uniquement l'onglet Coach**.

**Question directrice du Coach :**
> « Dans quelles situations la fenêtre se referme-t-elle le moins ? »

Autrement dit : quelles **couvertures** et quelles **routes** laissent la fenêtre
**rester ouverte** (faille défensive / opportunité offensive), ajusté sur **down & distance**.

---

## User stories (format EARS)

> **Principe :** le coach raisonne **en yards concrets** (receveur ouvert / couvert),
> pas en indice abstrait. Toutes les valeurs sont exprimées en **yards de séparation**
> et en **langage football** (Contesté / Serré / Ouvert / Grand ouvert).

### US-C1 — Vue matricielle des situations (en yards)
**En tant que** coach,
**je veux** voir une matrice couverture × route affichant la **séparation en yards à l'arrivée**,
**afin de** repérer d'un coup d'œil les situations où mon receveur finit **ouvert**.

- WHEN l'onglet Coach est ouvert, THE SYSTEM SHALL afficher une matrice
  dont les lignes sont les schémas de couverture et les colonnes les routes.
- THE SYSTEM SHALL afficher dans chaque cellule la **séparation en yards** (`separation`)
  et la colorer selon le libellé football (rouge = Contesté, vert foncé = Grand ouvert).

### US-C2 — Filtrage par situation
**En tant que** coach,
**je veux** filtrer par man/zone, profondeur, down et distance,
**afin d'** adapter l'analyse au contexte de jeu que je prépare.

- WHEN le coach applique un filtre (man/zone, profondeur, down, distance),
  THE SYSTEM SHALL recalculer la matrice sur le sous-ensemble correspondant.
- THE SYSTEM SHALL recalculer les moyennes via `Σ sum_* / Σ n`
  (jamais une moyenne de moyennes).

### US-C3 — Fiabilité de l'échantillon
**En tant que** coach,
**je veux** ne pas être induit en erreur par des cellules à faible échantillon,
**afin de** ne décider que sur des tendances solides.

- IF une cellule a `n < 10`, THEN THE SYSTEM SHALL la griser
  et afficher « échantillon insuffisant ».

### US-C4 — Détail d'une cellule
**En tant que** coach,
**je veux** voir le détail chiffré d'une situation,
**afin de** justifier ma décision.

- WHEN le coach survole/clique une cellule, THE SYSTEM SHALL afficher en langage football :
  la séparation à l'arrivée (`separation` + `separation_label`),
  le `% ouvert` et le `% contesté`, l'évolution « fenêtre passée de X → Y yd »,
  `n` et l'intervalle de confiance `ci`.

---

## Hors périmètre (pour cet onglet)
- Classement individuel des défenseurs → onglet Scout.
- Animation d'une action → onglet Broadcast.

## Limites / biais à afficher
- Seuil `n ≥ 10` par cellule.
- Routes nettoyées via **liste blanche** (voir design.md).
- Analyse descriptive (ne prédit pas) ; valable sur n'importe quelle saison au même format.
