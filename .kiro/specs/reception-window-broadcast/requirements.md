# Requirements — Onglet Broadcast (Fenêtre de réception)

## Contexte
Même moteur « fenêtre de réception » que les autres onglets
(= séparation receveur ciblé ↔ défenseur le plus proche).
Ce document couvre **uniquement l'onglet Broadcast** (persona : narration / commentateur).

**Question directrice du commentateur :**
> « Que s'est-il passé pendant le vol de ce ballon ? »

**Principe :** raconter **une action réelle** de façon visuelle et factuelle — la fenêtre qui
évolue entre le lancer et l'arrivée, en **yards**, avec une phrase générée automatiquement.

---

## User stories (format EARS)

### US-B1 — Animation d'une action
**En tant que** commentateur,
**je veux** voir l'animation d'une action (receveur, défenseur, ballon) sur le terrain,
**afin de** montrer visuellement ce qui s'est passé pendant le vol.

- WHEN une action est sélectionnée, THE SYSTEM SHALL animer, frame par frame,
  les positions du receveur ciblé, du défenseur le plus proche et du ballon.
- THE SYSTEM SHALL tracer la **fenêtre** (segment receveur ↔ défenseur) à chaque frame.

### US-B2 — Fenêtre qui évolue en direct
**En tant que** commentateur,
**je veux** voir la valeur de la fenêtre (en yd) évoluer pendant l'animation,
**afin de** commenter le moment où elle se referme.

- THE SYSTEM SHALL afficher un compteur de la fenêtre (yd) synchronisé avec l'animation.
- THE SYSTEM SHALL afficher une courbe simple de `window_series` (fenêtre par frame).

### US-B3 — Phrase factuelle auto-générée
**En tant que** commentateur,
**je veux** une phrase prête à dire, générée à partir des chiffres,
**afin de** commenter en une seconde sans calcul.

- WHEN l'action est chargée, THE SYSTEM SHALL générer une phrase du type
  « Fenêtre réduite de 6,1 à 0,9 yd en 1,2 s » (ou « élargie de … » si la fenêtre s'ouvre).
- THE SYSTEM SHALL afficher le résultat de l'action (passe complète / incomplète…).

### US-B4 — Sélection d'une action
**En tant que** commentateur,
**je veux** choisir l'action à visualiser,
**afin de** préparer ou illustrer un moment précis.

- THE SYSTEM SHALL proposer une liste d'actions sélectionnables (par match / description).

---

## Hors périmètre
- Agrégation par situation → onglet Coach.
- Classement des défenseurs → onglet Scout.

## Limites à afficher
- Position du **ballon** approximée (trajectoire lancer → `ball_land`), les positions des **joueurs**
  sont réelles (`output`).
- Une action à la fois (vue narrative, pas statistique).
