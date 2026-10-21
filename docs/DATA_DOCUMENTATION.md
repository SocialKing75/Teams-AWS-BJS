# Documentation des données

Source : documentation officielle NFL Big Data Bowl (tracking fourni par NFL Next Gen Stats, scouting par Pro Football Focus), reproduite telle quelle en section 2.

## 1. Correspondance avec les fichiers réellement fournis pour la compétition

La documentation ci-dessous décrit le format « classique » du Big Data Bowl (un fichier par table : games, plays, players, pffScoutingData, tracking par match). Les fichiers livrés dans l'archive `114239_nfl_competition_files_published_analytics_final.zip` suivent le format 2026, plus compact. Table de passage vérifiée sur les données :

| Fichier livré | Équivalent dans la documentation | Clés | Remarques |
|---|---|---|---|
| `supplementary_data.csv` (18 009 lignes) | games.csv + plays.csv fusionnés | `game_id`, `play_id` | Noms en snake_case (`gameId` → `game_id`). Contient aussi 3 901 actions de la saison 2024 sans tracking ; seules les 14 108 actions 2023 ont du tracking. |
| `train/input_2023_wXX.csv` (18 fichiers) | tracking_[gameId].csv + players.csv | `game_id`, `play_id`, `nfl_id`, `frame_id` | Tracking à 10 images/s du snap jusqu'au lancer. Pas de ligne « ballon » : le point de chute est donné par `ball_land_x` / `ball_land_y`. Infos joueur (`player_name`, `player_height`, `player_weight`, `player_birth_date`, `player_position`) intégrées. Pas de colonnes `time`, `dis`, `event`, `jerseyNumber`. |
| `train/output_2023_wXX.csv` (18 fichiers) | tracking pendant le vol du ballon | `game_id`, `play_id`, `nfl_id`, `frame_id` | Uniquement `x`, `y`, pour les joueurs marqués `player_to_predict = True` dans input (receveur ciblé + défenseurs proches du point de chute). Le nombre de frames est `num_frames_output` (10 par seconde). |

Colonnes de `supplementary_data.csv` et leur équivalent documenté :

| Fichier livré | Documentation | Différence |
|---|---|---|
| `pass_result` | `passResult` | Seules les valeurs C, I, IN sont présentes (pas de sacks S ni de scrambles R : le jeu ne contient que des passes lancées). |
| `pre_penalty_yards_gained`, `yards_gained` | `prePenaltyPlayResult`, `playResult` | |
| `team_coverage_type`, `team_coverage_man_zone` | `pff_passCoverage`, `pff_passCoverageType` | Valeurs : COVER_0_MAN, COVER_1_MAN, COVER_2_MAN, COVER_2_ZONE, COVER_3_ZONE, COVER_4_ZONE (= Quarters), COVER_6_ZONE, PREVENT. |
| `play_action` | `pff_playAction` | |
| `dropback_type`, `dropback_distance` | `dropBackType` | |
| `defenders_in_the_box` | `defendersInBox` | |
| `offense_formation`, `receiver_alignment`, `route_of_targeted_receiver`, `pass_length`, `pass_location_type` | non documentés dans l'ancien format | `pass_length` en yards (peut être négatif), `receiver_alignment` du type « 3x1 ». |
| `expected_points`, `expected_points_added`, probabilités de victoire | non documentés dans l'ancien format | `visitor_team_win_probility_added` : faute de frappe d'origine conservée. |

Colonnes de `input_*.csv` :

| Fichier livré | Documentation | Différence |
|---|---|---|
| `x`, `y`, `s`, `a`, `o`, `dir`, `play_direction`, `frame_id` | identiques (voir Figure 1 : x de 0 à 120 yd, y de 0 à 53,3 yd, vitesse en yd/s, accélération en yd/s², angles en degrés) | |
| `player_side` (Offense / Defense), `player_role` | `pff_role` | Valeurs : Passer, Targeted Receiver, Other Route Runner, Defensive Coverage. Pas de rôle Pass block / Pass rush : les bloqueurs et rushers ne sont pas dans le tracking. |
| `absolute_yardline_number` | `absoluteYardlineNumber` | |
| `player_to_predict`, `num_frames_output`, `ball_land_x`, `ball_land_y` | propres au format 2026 | Le point de chute peut être hors terrain (passe hors limites). |

Codes équipes présents (32) : ARI, ATL, BAL, BUF, CAR, CHI, CIN, CLE, DAL, DEN, DET, GB, HOU, IND, JAX, KC, LA, LAC, LV, MIA, MIN, NE, NO, NYG, NYJ, PHI, PIT, SEA, SF, TB, TEN, WAS. Les descriptions textuelles d'action utilisent parfois d'autres codes (ARZ, BLT…), non utilisés par le code.

## 2. Documentation officielle (reproduite sans modification)

Data Documentation
Description
Here, you'll find a summary of each data set for this compeition, a list of key variables to join on, and a description of each variable. The tracking data is provided by the NFL Next Gen Stats team. The Scouting data is provided by Pro Football Focus.

This competition allows participants to use supplemental NFL data as long as it is free and publicly available to all participants. Examples of sources that could be used include nflverse and Pro Football Reference. Please note that the gameId and playId of the Big Data Bowl data merge with the old_game_id and play_id of nflverse's play-by-play data.

File descriptions
Game data: The games.csv contains the teams playing in each game. The key variable is gameId.

Play data: The plays.csv file contains play-level information from each game. The key variables are gameId and playId.

Player data: The players.csv file contains player-level information from players that participated in any of the tracking data files. The key variable is nflId.

PFF Scouting data: The pffScoutingData.csv file contains player-level scouting information for each game and play. The key variables are gameId, playId, and nflId.

Tracking data: Files tracking_[gameId].csv contain player tracking data from season [gameId]. The key variables are gameId, playId, and nflId.

Game data
gameId: Game identifier, unique (numeric)
season: Season of game
week: Week of game
gameDate: Game Date (time, mm/dd/yyyy)
gameTimeEastern: Start time of game (time, HH:MM:SS, EST)
homeTeamAbbr: Home team three-letter code (text)
visitorTeamAbbr: Visiting team three-letter code (text)
Play data
gameId: Game identifier, unique (numeric)
playId: Play identifier, not unique across games (numeric)
playDescription: Description of play (text)
quarter: Game quarter (numeric)
down: Down (numeric)
yardsToGo: Distance needed for a first down (numeric)
possessionTeam: Team abbr of team on offense with possession of ball (text)
defensiveTeam: Team abbr of team on defense (text)
yardlineSide: 3-letter team code corresponding to line-of-scrimmage (text)
yardlineNumber: Yard line at line-of-scrimmage (numeric)
gameClock: Time on clock of play (MM:SS)
preSnapHomeScore: Home score prior to the play (numeric)
preSnapVisitorScore: Visiting team score prior to the play (numeric)
passResult: Dropback outcome of the play (C: Complete pass, I: Incomplete pass, S: Quarterback sack, IN: Intercepted pass, R: Scramble, text)
penaltyYards: yards gained by offense by penalty (numeric)
prePenaltyPlayResult: Net yards gained by the offense, before penalty yardage (numeric)
playResult: Net yards gained by the offense, including penalty yardage (numeric)
foulName[i]: Name of the i-th penalty committed during the play. i ranges between 1 and 3 (text)
foulNFLId[i]: nflId of the player who comitted the i-th penalty during the play. i ranges between 1 and 3 (numeric)
absoluteYardlineNumber: Distance from end zone for possession team (numeric)
offenseFormation: Formation used by possession team (text)
personnelO: Personnel used by offensive team (text)
defendersInBox: Number of defenders in close proximity to line-of-scrimmage (numeric)
personnelD: Personnel used by defensive team (text)
dropBackType: Dropback categorization of quarterback (text)
pff_playAction: indicator for whether offense executes play action fake on the play. Variable provided by PFF (binary)
pff_passCoverage: Coverage scheme of defense. Variable provided by PFF (text)
Possible values:
Cover-0: A Man to Man coverage across the board with no deep defenders. This coverage is typically accompanied with a blitz
Cover-1: When a defense plays any form of Man defense across the board with a Defensive Player as a Single High Man concept
Cover-2: A two deep safety concept where any zone principle is applied
2-Man: A two deep safety concept where a man principle is applied
Cover-3: Any 3 Deep, 4 Under concept
Quarters: A Quarters concept on both halves of the field. In general it will be a 4 Deep, 3 Under concept where the corners are on #1, safeties on #2, and backside safety rotation dependent on formation
Cover-6: A Quarters Concept on half the field and a 2 Deep concept on the other half
Bracket: Recorded in the field and up to the 12 yard line in the red zone – when two offensive players have an in and out bracket by two defenders
Goal Line: Calls where a Goal Line defense is used.
Red Zone: Calls that are typically specific to the Red Zone and do not occur in the field often
Prevent: Special end of half or end of game situations where a Prevent defense is utilized
Miscellaneous: Coverage concepts that we feel do not comfortably fit into any of our coverage categories
pff_passCoverageType: Whether defense's coverage type was man, zone or other. Variable provided by PFF (text)
Player data
nflId: Player identification number, unique across players (numeric)
height: Player height (text)
weight: Player weight (numeric)
birthDate: Date of birth (YYYY-MM-DD)
collegeName: Player college (text)
officialPosition: Official player position (text)
displayName: Player name (text)
PFF Scouting data
gameId: Game identifier, unique (numeric)
playId: Play identifier, not unique across games (numeric)
nflId: Player identification number, unique across players (numeric)
pff_role: The player's role on this play (text)
Possible values:
Coverage: Defensive player. Player whose initial goal is to play man or zone coverage
Pass: Offensive player. Player identified as the passer
Pass block: Offensive player. Anyone fully blocking a defender from the QB, or anyone in a clear pass block stance
Pass route: Offensive player. Any player not identified as a Pass Blocker or Passer
Pass rush: Defensive player. Any player whose initial intent is to rush the passer
pff_positionLinedUp: Position that the player was aligned at the snap of the ball on this play (text)
pff_hit: If player is a defensive player, indicator for whether they are credited with recording a hit on this play (binary)
pff_hurry: If player is a defensive player, indicator for whether they are credited with recording a hurry on this play (binary)
pff_sack: If player is a defensive player, indicator for whether they are credited with recording a sack on this play (binary)
pff_beatenByDefender: If player is a blocking offensive player, indicator for whether they are by a defender but was not charged for yielding a hit, hurry or sack (binary)
pff_hitAllowed: If player is a blocking offensive player, indicator for whether they are responsible for a hit on the QB (binary)
pff_hurryAllowed: If player is a blocking offensive player, indicator for whether they are responsible for a hurry on the QB (binary)
pff_sackAllowed: If player is a blocking offensive player, indicator for whether they are responsible for a sack on the QB (binary)
pff_nflIdBlockedPlayer: If player is a blocking offensive player, the nflId of the first defender the offensive player blocked (numeric)
pff_blockType: If player is a blocking offensive player, the type of block that the offensive player is executing on the defender (text)
Possible values:
BH: Backfield Help - A block from a player aligned in the backfield on which the blocker merely helps on a block rather than fully engaging his assignment. Usually seen when a blocker is clearing up a block or picking up a defender when he has broken through or been missed by another blocker
CH: Chip Block - This is only to be used for players who chip a pass rusher when they release for their route
CL: Second Level – A block made at the second level, this must be at least two yards across the line of scrimmage
NB: No Block - If a blocker executes no block on a play but simply runs his path or takes his pass set then we will note him with one all blocking line with this block type
PA: Play Action Pass Protection - A blocker pass protecting inline on a play action pass selling the play action by stepping in to show a run block before converting to pass protect
PP: Pass Protection - A standard pass protection block from an inline blocker
PR: Pocket Roll Block - This block type will be used any time the offense is executing a "rolling pocket" by which the entire offensive line moves with the QB's rollout to stay in front of him but without ever taking a "conventional" pass set. There will be flexibility here to record the PR – Pocket Roll Block type in the same way as PA & RP block types in that individual matchups & responsibilities won't always be obvious or necessary, so PR block types can be recorded by multiple blockers on an individual defender on the same play
PT: Post Block - A post block by an offensive player in pass protection to control a defender for another blocker while clearly demonstrating that he is not, at least initially, trying to fully engage with the block
PU: Backfield Pickup - A pass protection pick-up by a player aligned in the backfield
SR: Set & Release - A blocker who sets to pass protect a defender before releasing. This block will cover both players releasing from a set to block for a screen as well as "hold ups" by tight ends before they leak into the flat
SW: Switch Block - A blocker who passes off (or attempts to pass off) a defender. Most often used on stunts but can also be used for pass offs when pass rushers are slanting across the pocket or interior defenders are working to the edge to replace a dropping edge rusher, with an interior offensive lineman passing them out rather than staying with them
UP: Pull Pass Protection - A blocker pulling in pass protection from an inline alignment to block a defender in pass protection
pff_backFieldBlock: If player is a blocking offensive player, indicator for whether block occured in offensive backfield.
Tracking data
Files tracking/tracking_[gameId].csv contain player and ball tracking data, one file per game (122 games across Weeks 1-8). To filter by week, join gameId to week in games.csv.

gameId: Game identifier, unique (numeric)
playId: Play identifier, not unique across games (numeric)
nflId: Player identification number, unique across players. When value is NA, row corresponds to ball. (numeric)
frameId: Frame identifier for each play, starting at 1 (numeric)
time: Time stamp of play (time, yyyy-mm-dd, hh:mm:ss)
jerseyNumber: Jersey number of player (numeric)
team: Team abbreviation of the corresponding player; value is football on ball rows (text)
playDirection: Direction that the offense is moving (left or right)
x: Player position along the long axis of the field, 0 - 120 yards. See Figure 1 below. (numeric)
y: Player position along the short axis of the field, 0 - 53.3 yards. See Figure 1 below. (numeric)
s: Speed in yards/second (numeric)
a: Acceleration in yards/second^2 (numeric)
dis: Distance traveled from prior time point, in yards (numeric)
o: Player orientation (deg), 0 - 360 degrees (numeric)
dir: Angle of player motion (deg), 0 - 360 degrees (numeric)
event: Tagged play details, including moment of ball snap, pass release, pass catch, tackle, etc (text)
Figure 1: Field coordinates, direction, and orientation
