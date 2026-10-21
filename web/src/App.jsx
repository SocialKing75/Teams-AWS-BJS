// Interface coach — fenêtre de réception, mobile-first (bord de terrain).
// Chaque écran est une scène sur un terrain (vue de dessus 2D ou caméra 3D) :
// le receveur court sa route, le défenseur le suit, le cercle blanc est la fenêtre
// de réception (rayon = distance au défenseur le plus proche), le cercle jaune la moyenne de la ligue.
// Tous les chiffres viennent de data.json, exporté des CSV par src/export_web.py.
import { Fragment, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import data from "./data.json";

const BLEU = "#2a78d6";
const ORANGE = "#eb6834";
const JAUNE = "#ffd84d"; // repère ligue, comme la ligne de premier down à la télé
const CONFIANCE = { elevee: "#008300", moyenne: "#c98500", faible: "#52514e" };
const LIB_CONF = { elevee: "élevée", moyenne: "moyenne", faible: "faible" };

const yd = (v, signe = false) => (signe && v > 0 ? "+" : "") + Number(v).toFixed(1) + " yd";
const info = (abr) => data.equipes_info[abr] || { nom: abr, surnom: abr, couleur: "#3a3a38", couleur2: "#c3c2b7", logo: null };
const lerp = (a, b, t) => a + (b - a) * t;
const norme = ([x, y]) => { const n = Math.hypot(x, y) || 1; return [x / n, y / n]; };
const chemin = (pts) => pts.map(([x, y], i) => `${i ? "L" : "M"}${x} ${-y}`).join(" ");

// Tracés schématiques des routes (yards ; x vers l'intérieur du terrain, y vers l'avant).
// Seuls les rayons des cercles sont des mesures : la forme de la route est illustrative.
const ROUTES = {
  GO: [[0, 0], [0, 22]], SLANT: [[0, 0], [0, 2], [7, 9]], OUT: [[0, 0], [0, 10], [-7, 10]],
  IN: [[0, 0], [0, 10], [10, 10]], POST: [[0, 0], [0, 10], [8, 20]], CORNER: [[0, 0], [0, 10], [-7, 18]],
  HITCH: [[0, 0], [0, 7], [0.8, 5.5]], FLAT: [[5, -1], [-4, 3]], CROSS: [[0, 0], [0, 4], [18, 7]],
  SCREEN: [[1, 0], [-2, -2.5]], ANGLE: [[4, -1], [1, 3], [8, 6]], WHEEL: [[4, -1], [-2, 2], [-4, 6], [-4, 17]],
};
const X0 = 10;            // position latérale du receveur au snap
const QB = [26.65, -7];   // quarterback au centre du terrain
const VUE = { x: 0, y: -9, w: 36, h: 36 };

/** Longueurs cumulées d'une ligne brisée. */
function cumul(pts) {
  const c = [0];
  for (let i = 1; i < pts.length; i++) c.push(c[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return c;
}

/** Point à la fraction f de la longueur d'une ligne brisée. */
function pointA(pts, f) {
  const c = cumul(pts);
  const cible = f * c[c.length - 1];
  for (let i = 1; i < pts.length; i++) {
    if (cible <= c[i] || i === pts.length - 1) {
      const t = c[i] > c[i - 1] ? Math.min(1, (cible - c[i - 1]) / (c[i] - c[i - 1])) : 0;
      return [lerp(pts[i - 1][0], pts[i][0], t), lerp(pts[i - 1][1], pts[i][1], t)];
    }
  }
  return pts[pts.length - 1];
}

/** Portion de la ligne brisée déjà parcourue (jusqu'à la fraction f). */
function jusqua(pts, f) {
  const c = cumul(pts);
  const cible = f * c[c.length - 1];
  return [...pts.filter((_, i) => c[i] < cible), pointA(pts, f)];
}

/** Horloge d'animation 0 → 1 en boucle, avec pause sur l'image finale ; figée si l'utilisateur réduit les animations. */
function useBoucle(duree = 2600, pause = 1600) {
  const [t, setT] = useState(1);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return undefined;
    let raf;
    const debut = performance.now();
    const tick = (now) => { setT(Math.min(1, ((now - debut) % (duree + pause)) / duree)); raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [duree, pause]);
  return t;
}

function Logo({ abr, taille = 40 }) {
  const [ko, setKo] = useState(false);
  const e = info(abr);
  if (!e.logo || ko) {
    return <span className="logo-badge" style={{ width: taille, height: taille, background: e.couleur, fontSize: taille * 0.34 }}>{abr}</span>;
  }
  return <img className="logo" src={e.logo} alt={e.nom} width={taille} height={taille} onError={() => setKo(true)} />;
}

/** Gazon : bandes tous les 5 yd, lignes de yards, hash marks, lignes de touche, ligne de mêlée.
 *  decalage : position de la ligne de mêlée modulo 5, pour aligner les lignes sur le vrai terrain. */
function Gazon({ vue, melee, decalage = 0 }) {
  const bandes = [];
  for (let y = Math.floor((vue.y + decalage) / 5) * 5 - decalage; y < vue.y + vue.h; y += 5) {
    const k = Math.round((y + decalage) / 5);
    bandes.push(<rect key={`b${k}`} x={vue.x} y={-(y + 5)} width={vue.w} height={5} fill={Math.abs(k) % 2 ? "#2f8a3a" : "#2a7d34"} />);
    bandes.push(<line key={`l${k}`} x1={Math.max(0, vue.x)} x2={Math.min(53.3, vue.x + vue.w)} y1={-y} y2={-y} stroke="#fff" strokeOpacity="0.55" strokeWidth="0.18" />);
  }
  const hash = [];
  for (let y = Math.ceil(vue.y); y < vue.y + vue.h; y++) {
    if ((y + Math.round(decalage)) % 5 === 0) continue;
    for (const x of [0.6, 23.58, 29.73, 52.04]) {
      if (x > vue.x && x < vue.x + vue.w) hash.push(<line key={`h${x}_${y}`} x1={x} x2={x + 0.66} y1={-y} y2={-y} stroke="#fff" strokeOpacity="0.5" strokeWidth="0.14" />);
    }
  }
  const haut = -(vue.y + vue.h);
  return (
    <g>
      {bandes}{hash}
      {vue.x < 0 && <rect x={vue.x} y={haut} width={-vue.x} height={vue.h} fill="#1f5e27" />}
      {vue.x + vue.w > 53.3 && <rect x={53.3} y={haut} width={vue.x + vue.w - 53.3} height={vue.h} fill="#1f5e27" />}
      {vue.x <= 0 && <line x1={0} x2={0} y1={haut} y2={-vue.y} stroke="#fff" strokeWidth="0.5" />}
      {vue.x + vue.w >= 53.3 && <line x1={53.3} x2={53.3} y1={haut} y2={-vue.y} stroke="#fff" strokeWidth="0.5" />}
      {melee && <line x1={Math.max(0, vue.x)} x2={Math.min(53.3, vue.x + vue.w)} y1={0} y2={0} stroke={BLEU} strokeWidth="0.4" />}
    </g>
  );
}

/** Conteneur de terrain : bascule entre vue de dessus et caméra 3D, habillage HTML par-dessus. */
function Terrain({ vue = VUE, d3, children, habillage, melee = true, decalage = 0 }) {
  const ratio = `${vue.w} / ${vue.h}`;
  return (
    <div className={`terrain ${d3 ? "d3" : ""}`} style={{ aspectRatio: d3 ? `${vue.w} / ${(vue.h * 0.86).toFixed(2)}` : ratio }}>
      <svg viewBox={`${vue.x} ${-(vue.y + vue.h)} ${vue.w} ${vue.h}`} style={{ aspectRatio: ratio }} preserveAspectRatio="xMidYMid meet" role="img">
        <Gazon vue={vue} melee={melee} decalage={decalage} />
        {children}
      </svg>
      {habillage}
    </div>
  );
}

/** Pion de joueur : défenseur aux couleurs et au logo de l'équipe, receveur en blanc. */
function Pion({ x, y, r, couleur, logo, receveur }) {
  const id = useId().replace(/:/g, "");
  return (
    <g>
      <ellipse cx={x + 0.25} cy={-y + 0.35} rx={r} ry={r * 0.8} fill="#000" opacity="0.28" />
      <circle cx={x} cy={-y} r={r} fill={receveur ? "#fff" : couleur} stroke={receveur ? "#0b0b0b" : "#fff"} strokeWidth="0.28" />
      {logo && !receveur && (
        <>
          <clipPath id={id}><circle cx={x} cy={-y} r={r * 0.8} /></clipPath>
          <circle cx={x} cy={-y} r={r * 0.8} fill="#fff" />
          <image href={logo} x={x - r * 0.8} y={-y - r * 0.8} width={r * 1.6} height={r * 1.6} clipPath={`url(#${id})`} />
        </>
      )}
    </g>
  );
}

/** Scène animée d'une route : fenêtre au lancer → fenêtre à l'arrivée, repère ligue en jaune. */
function SceneRoute({ route, fl, fa, ligue, abr, d3 }) {
  const t = useBoucle();
  const e = info(abr);
  const pts = (ROUTES[route] || ROUTES.GO).map(([x, y]) => [X0 + x, y]);
  const LANCER = 0.3; // part de l'animation avant le lancer
  const fRoute = t < LANCER ? (t / LANCER) * 0.5 : 0.5 + ((t - LANCER) / (1 - LANCER)) * 0.5;
  const vol = t < LANCER ? 0 : (t - LANCER) / (1 - LANCER);
  const P0 = pointA(pts, 0.5);
  const P1 = pointA(pts, 1);
  const R = pointA(pts, fRoute);
  const u0 = norme([0.6, 0.8]);
  const u1 = norme([0.85, 0.5]);
  const D0 = [P0[0] + u0[0] * fl, P0[1] + u0[1] * fl];
  const D1 = [P1[0] + u1[0] * fa, P1[1] + u1[1] * fa];
  const Dsnap = [D0[0] + 1.5, D0[1] + 3];
  const D = t < LANCER
    ? [lerp(Dsnap[0], D0[0], t / LANCER), lerp(Dsnap[1], D0[1], t / LANCER)]
    : [lerp(D0[0], D1[0], vol), lerp(D0[1], D1[1], vol)];
  const fenetre = Math.hypot(R[0] - D[0], R[1] - D[1]);
  const xs = [...pts.map((p) => p[0]), D0[0], D1[0], P1[0] - ligue, P1[0] + ligue];
  const ys = [...pts.map((p) => p[1]), D0[1], D1[1], P1[1] + ligue + 6, -3];
  const cote = Math.max(Math.max(...xs) - Math.min(...xs) + 8, Math.max(...ys) - Math.min(...ys) + 6, 22);
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2;
  const cy = (Math.max(...ys) + Math.min(...ys)) / 2;
  const vue = { x: Math.max(-2, cx - cote / 2), y: cy - cote / 2, w: cote, h: cote };
  // Ballon : arc entre le quarterback et le point d'arrivée, ombre au sol
  const C = [(QB[0] + P1[0]) / 2, (QB[1] + P1[1]) / 2];
  const B = [0, 1].map((k) => (1 - vol) ** 2 * QB[k] + 2 * (1 - vol) * vol * C[k] + vol ** 2 * P1[k]);
  const haut = 4 * vol * (1 - vol) * (2.5 + Math.hypot(P1[0] - QB[0], P1[1] - QB[1]) / 8);
  const phase = t < LANCER ? "avant le lancer" : t < 1 ? "ballon en l'air" : "arrivée du ballon";
  return (
    <Terrain vue={vue} d3={d3} habillage={
      <div className="habillage">
        <div className="puce-fenetre"><span>{phase}</span><b>{t < LANCER ? "—" : yd(fenetre)}</b></div>
      </div>
    }>
      <path d={chemin(pts)} fill="none" stroke="#fff" strokeOpacity="0.5" strokeWidth="0.3" strokeDasharray="0.8 0.6" />
      <path d={chemin(jusqua(pts, fRoute))} fill="none" stroke="#fff" strokeWidth="0.35" />
      <circle cx={P1[0]} cy={-P1[1]} r={ligue} fill="none" stroke={JAUNE} strokeWidth="0.32" strokeDasharray="0.9 0.5" />
      <text x={P1[0]} y={-P1[1] - ligue - 0.6} className="svg-etiquette" fill={JAUNE} textAnchor="middle">ligue {ligue.toFixed(1)}</text>
      {t >= LANCER && <circle cx={R[0]} cy={-R[1]} r={fenetre} fill="#fff" fillOpacity="0.16" stroke="#fff" strokeWidth="0.3" />}
      <Pion x={QB[0]} y={QB[1]} r={1.1} receveur />
      <Pion x={R[0]} y={R[1]} r={1.15} receveur />
      <Pion x={D[0]} y={D[1]} r={1.5} couleur={e.couleur} logo={e.logo} />
      {vol > 0 && vol < 1 && (
        <g>
          <ellipse cx={B[0]} cy={-B[1]} rx="0.6" ry="0.35" fill="#000" opacity="0.3" />
          <ellipse cx={B[0]} cy={-B[1] - haut} rx="0.75" ry="0.45" fill="#7a3e12" stroke="#fff" strokeWidth="0.12" />
        </g>
      )}
    </Terrain>
  );
}

/** Point à la fraction f d'une suite d'images (interpolation entre images voisines). */
function aImage(pts, f) {
  if (pts.length < 2) return pts[0];
  const i = Math.min(pts.length - 1, Math.max(0, f * (pts.length - 1)));
  const k = Math.min(pts.length - 2, Math.floor(i));
  const u = i - k;
  return [lerp(pts[k][0], pts[k + 1][0], u), lerp(pts[k][1], pts[k + 1][1], u)];
}

/** Action réelle (play.json) : trajectoires mesurées du receveur ciblé et du défenseur suivi,
 *  avant le lancer puis pendant le vol ; ballon interpolé du passeur au point de chute. */
function SceneReelle({ action, ligue, abr, d3 }) {
  const t = useBoucle(3400, 1800);
  const e = info(abr);
  const los = action.los_x;
  const P = ([X, Y]) => [Y, X - los]; // écran : x = largeur du terrain, y = yards depuis la ligne de mêlée
  const rPre = [...action.receiver_path, action.frames[0].receiver].map(P);
  const dPre = [...action.defender_path, action.frames[0].defender].map(P);
  const rVol = action.frames.map((f) => P(f.receiver));
  const dVol = action.frames.map((f) => P(f.defender));
  const bVol = action.frames.map((f) => P(f.ball));
  const LANCER = 0.4;
  const avant = t < LANCER;
  const fv = avant ? 0 : (t - LANCER) / (1 - LANCER);
  const R = avant ? aImage(rPre, t / LANCER) : aImage(rVol, fv);
  const D = avant ? aImage(dPre, t / LANCER) : aImage(dVol, fv);
  const B = aImage(bVol, fv);
  const fin = rVol[rVol.length - 1];
  const haut = 4 * fv * (1 - fv) * (2 + Math.hypot(bVol[0][0] - fin[0], bVol[0][1] - fin[1]) / 8);
  const fenetre = Math.hypot(R[0] - D[0], R[1] - D[1]);
  // Cadrage : toute l'action, avec la marge du repère ligue
  const tous = [...rPre, ...dPre, ...rVol, ...dVol, P(action.passer), P(action.ball_land)];
  const xs = [...tous.map((p) => p[0]), fin[0] - ligue, fin[0] + ligue];
  const ys = [...tous.map((p) => p[1]), fin[1] + ligue + 4];
  const cote = Math.max(Math.max(...xs) - Math.min(...xs) + 6, Math.max(...ys) - Math.min(...ys) + 5, 20);
  const vue = { x: (Math.max(...xs) + Math.min(...xs)) / 2 - cote / 2, y: (Math.max(...ys) + Math.min(...ys)) / 2 - cote / 2, w: cote, h: cote };
  const phase = avant ? "avant le lancer" : t < 1 ? "ballon en l'air" : "arrivée du ballon";
  const qb = P(action.passer);
  const chute = P(action.ball_land);
  return (
    <Terrain vue={vue} d3={d3} decalage={((los % 5) + 5) % 5} habillage={
      <div className="habillage">
        <div className="puce-fenetre"><span>{phase}</span><b>{yd(fenetre)}</b></div>
        <div className="puce-reelle">Action réelle</div>
      </div>
    }>
      <path d={chemin([...rPre, ...rVol.slice(1)])} fill="none" stroke="#fff" strokeOpacity="0.55" strokeWidth="0.3" strokeDasharray="0.8 0.6" />
      <path d={chemin([...dPre, ...dVol.slice(1)])} fill="none" stroke={e.couleur2} strokeOpacity="0.85" strokeWidth="0.25" strokeDasharray="0.5 0.5" />
      <circle cx={fin[0]} cy={-fin[1]} r={ligue} fill="none" stroke={JAUNE} strokeWidth="0.32" strokeDasharray="0.9 0.5" />
      <text x={fin[0]} y={-fin[1] - ligue - 0.6} className="svg-etiquette" fill={JAUNE} textAnchor="middle">ligue {ligue.toFixed(1)}</text>
      <circle cx={R[0]} cy={-R[1]} r={fenetre} fill="#fff" fillOpacity="0.16" stroke="#fff" strokeWidth="0.3" />
      <circle cx={chute[0]} cy={-chute[1]} r="0.45" fill="none" stroke="#fff" strokeWidth="0.15" />
      <Pion x={qb[0]} y={qb[1]} r={1.05} receveur />
      <Pion x={R[0]} y={R[1]} r={1.15} receveur />
      <Pion x={D[0]} y={D[1]} r={1.5} couleur={e.couleur} logo={e.logo} />
      {!avant && fv < 1 && (
        <g>
          <ellipse cx={B[0]} cy={-B[1]} rx="0.6" ry="0.35" fill="#000" opacity="0.3" />
          <ellipse cx={B[0]} cy={-B[1] - haut} rx="0.75" ry="0.45" fill="#7a3e12" stroke="#fff" strokeWidth="0.12" />
        </g>
      )}
    </Terrain>
  );
}

/** Carte « une information » : route, écart à la ligue en grand, action réelle animée. */
function CarteRoute({ c, abr, d3, action }) {
  const coul = c.type === "attaquer" ? BLEU : ORANGE;
  const lig = data.ligue_routes.find((l) => l.route === c.route);
  const ligue = lig ? lig.fenetre_arrivee : c.fenetre_ligue;
  return (
    <article className="carte" style={{ "--accent": coul }}>
      <header className="carte-tete">
        <div>
          <div className="carte-route">{c.route}</div>
          <div className="carte-verbe">{c.type === "attaquer" ? "à attaquer" : "à éviter"}</div>
        </div>
        <div className="carte-chiffre">{yd(c.ecart_vs_ligue, true)}<small>vs ligue</small></div>
      </header>
      {action ? <SceneReelle action={action} ligue={ligue} abr={abr} d3={d3} />
        : <SceneRoute route={c.route} fl={c.fenetre_lancer_moy} fa={c.fenetre_arrivee_moy} ligue={ligue} abr={abr} d3={d3} />}
      {action && (
        <p className="carte-action">
          <b>{action.sentence}</b><br />
          Semaine {action.week} · {action.coverage_type} · {action.down}{action.down === 1 ? "er" : "e"} &amp; {action.yards_to_go} · {action.defender_name} ({action.defender_position}) sur {action.receiver_name}
        </p>
      )}
      <p className="carte-detail">
        Moyenne de cette défense sur la route : <b>{yd(c.fenetre_lancer_moy)}</b> au lancer → <b>{yd(c.fenetre_arrivee_moy)}</b> à l'arrivée · {c.n_actions} passes · {Math.round(c.taux_completion * 100)} % complétées
      </p>
      <p className="carte-detail">Confiance <span className="badge" style={{ background: CONFIANCE[c.confiance] }}>{LIB_CONF[c.confiance]}</span></p>
    </article>
  );
}

/** Cible vue de dessus : anneau au lancer, disque à l'arrivée, repère ligue en jaune. */
function Cible({ titre, ligne, ligue, couleur, d3, abr }) {
  const X = 20; // centre de la cible, entre la touche et les hash marks
  const vue = { x: X - 8, y: -8, w: 16, h: 16 };
  const e = info(abr);
  return (
    <figure className="cible">
      <Terrain vue={vue} d3={d3} melee={false}>
        {ligne && (
          <>
            <circle cx={X} cy="0" r={ligne.fenetre_lancer_moy} fill="none" stroke="#fff" strokeWidth="0.2" strokeDasharray="0.5 0.35" />
            <circle cx={X} cy="0" r={ligne.fenetre_arrivee_moy} fill={couleur} fillOpacity="0.6" stroke="#fff" strokeWidth="0.24" />
          </>
        )}
        {ligue && <circle cx={X} cy="0" r={ligue.fenetre_arrivee_moy} fill="none" stroke={JAUNE} strokeWidth="0.24" strokeDasharray="0.6 0.35" />}
        <Pion x={X} y={0} r={0.8} receveur />
        {ligne && <Pion x={X + ligne.fenetre_arrivee_moy * 0.72} y={ligne.fenetre_arrivee_moy * 0.69} r={1} couleur={e.couleur} logo={e.logo} />}
      </Terrain>
      <figcaption>
        <b>{titre}</b>
        <span className="cible-chiffre">{ligne ? yd(ligne.fenetre_arrivee_moy) : "—"}</span>
        <span>{ligne ? `${yd(ligne.fenetre_lancer_moy)} au lancer · n=${ligne.n_actions}` : "moins de 15 passes"}</span>
        {ligue && <span className="jaune">ligue {yd(ligue.fenetre_arrivee_moy)}</span>}
      </figcaption>
    </figure>
  );
}

/** Toutes les routes de la défense : écart à la ligue à l'arrivée ; barre vers la droite = plus ouverte que la ligue. */
function ToutesRoutes({ abr }) {
  const lignes = data.equipes_routes.filter((r) => r.defensive_team === abr).sort((a, b) => b.ecart_vs_ligue - a.ecart_vs_ligue);
  const max = Math.max(0.5, ...lignes.map((r) => Math.abs(r.ecart_vs_ligue)));
  return (
    <div className="toutes-routes">
      <h2 className="titre-groupe">Toutes les routes contre {info(abr).surnom}</h2>
      {lignes.length === 0 ? <p className="info">Aucune route avec assez de passes pour cette défense.</p> : (
        <ul>
          {lignes.map((r) => {
            const l = (Math.abs(r.ecart_vs_ligue) / max) * 50;
            return (
              <li key={r.route} title={`${r.route} : ${yd(r.fenetre_lancer_moy)} au lancer → ${yd(r.fenetre_arrivee_moy)} à l'arrivée · ligue ${yd(r.fenetre_ligue)}`}>
                <span className="tr-route">{r.route}</span>
                <span className="tr-barre" aria-hidden="true">
                  <i style={{ left: r.ecart_vs_ligue >= 0 ? "50%" : `${50 - l}%`, width: `${l}%`, background: r.ecart_vs_ligue >= 0 ? BLEU : ORANGE }} />
                </span>
                <span className="tr-chiffre">{yd(r.ecart_vs_ligue, true)}</span>
                <span className="tr-detail">{yd(r.fenetre_arrivee_moy)} à l'arrivée · {r.n_actions} passes · {pct(r.taux_completion)} complétées</span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="note">Écart à la moyenne de la ligue sur la même route, fenêtre à l'arrivée du ballon. Vers la droite : plus ouverte que la ligue. Routes avec moins de 15 passes masquées.</p>
    </div>
  );
}

const CASES_MZ = [["MAN_COVERAGE", "Courte"], ["MAN_COVERAGE", "Profonde"], ["ZONE_COVERAGE", "Courte"], ["ZONE_COVERAGE", "Profonde"]];
const trouveMZ = (rows, mz, prof) => rows.find((r) => r.team_coverage_man_zone === mz && r.profondeur.startsWith(prof));

function EcranManZone({ abr, comparer, d3 }) {
  const colonne = (a) => (
    <div className="colonne-mz">
      <h3 className="titre-equipe"><Logo abr={a} taille={32} /> {info(a).surnom}</h3>
      <div className="grille-cibles">
        {CASES_MZ.map(([mz, prof]) => (
          <Cible key={mz + prof} abr={a} d3={d3} titre={`${mz === "MAN_COVERAGE" ? "Man" : "Zone"} · ${prof.toLowerCase()}`}
            couleur={mz === "MAN_COVERAGE" ? BLEU : ORANGE}
            ligne={trouveMZ(data.equipes.filter((x) => x.defensive_team === a), mz, prof)}
            ligue={trouveMZ(data.synthese, mz, prof)} />
        ))}
      </div>
    </div>
  );
  return (
    <section>
      <h2 className="titre-ecran">Où sa couverture laisse de l'air</h2>
      <p className="legende-scene"><i className="pastille blanc" /> disque : fenêtre à l'arrivée · <i className="pastille pointille" /> au lancer · <i className="pastille jaune" /> moyenne ligue</p>
      <div className={`comparaison ${comparer ? "deux" : ""}`}>
        {colonne(abr)}
        {comparer && colonne(comparer)}
      </div>
      <p className="note">Courte : passe de moins de 15 yd ; profonde : 15 yd et plus.</p>
    </section>
  );
}

// ---- Onglet Matrice : contrat matchups.json (.kiro/specs/reception-window-coach/design.md) ----
const ORDRE_COUV = ["Cover-0", "Cover-1", "2-Man", "Cover-2", "Cover-3", "Quarters", "Cover-6", "Prevent"];
const ABR_COUV = { "Cover-0": "C0", "Cover-1": "C1", "2-Man": "2M", "Cover-2": "C2", "Cover-3": "C3", "Quarters": "Q", "Cover-6": "C6", "Prevent": "PV" };
const ORDRE_ROUTES = ["GO", "POST", "CORNER", "WHEEL", "CROSS", "IN", "OUT", "SLANT", "ANGLE", "HITCH", "FLAT", "SCREEN"];
const COUL_SEP = { "Contesté": ["#d03b3b", "#fff"], "Serré": ["#ec835a", "#0b0b0b"], "Ouvert": ["#8fd18f", "#0b0b0b"], "Grand ouvert": ["#1b7a33", "#fff"] };
const libSep = (v) => (v < 1 ? "Contesté" : v < 2 ? "Serré" : v < 3 ? "Ouvert" : "Grand ouvert");
const pct = (v) => `${Math.round(v * 100)} %`;
const SEUIL_N = 10;

/** Ré-agrégation du spec : Σ sum / Σ n, jamais une moyenne de moyennes. IC : bootstrap du contrat
 *  si la case vient d'une seule ligne, sinon approximation normale à partir des sommes de carrés. */
function agreger(lignes) {
  const s = lignes.reduce((a, r) => ({ n: a.n + r.n, wt: a.wt + r.sum_window_throw, wa: a.wa + r.sum_window_arrival, c: a.c + r.sum_closing,
    c2: a.c2 + r.sum_closing_sq, o: a.o + r.n_open, k: a.k + r.n_contested, ep: a.ep + r.sum_epa }), { n: 0, wt: 0, wa: 0, c: 0, c2: 0, o: 0, k: 0, ep: 0 });
  if (!s.n) return null;
  const moy = s.c / s.n;
  const et = Math.sqrt(Math.max(0, s.c2 / s.n - moy * moy) / s.n);
  return { n: s.n, sep: s.wa / s.n, lancer: s.wt / s.n, fermeture: moy, ouvert: s.o / s.n, conteste: s.k / s.n, epa: s.ep / s.n,
    ic: lignes.length === 1 ? lignes[0].ci : [moy - 1.96 * et, moy + 1.96 * et], icBoot: lignes.length === 1 };
}

function EcranMatrice({ matchups, d3 }) {
  const [mz, setMz] = useState("tous");
  const [prof, setProf] = useState("tous");
  const [down, setDown] = useState("tous");
  const [dist, setDist] = useState("tous");
  const [sel, setSel] = useState(null);
  // Changer un filtre ferme la fiche : ses chiffres ne correspondraient plus à la sélection
  const filtrer = (changer) => (v) => { changer(v); setSel(null); };
  useEffect(() => {
    if (!sel) return undefined;
    const echap = (ev) => ev.key === "Escape" && setSel(null);
    window.addEventListener("keydown", echap);
    return () => window.removeEventListener("keydown", echap);
  }, [sel]);
  // En 3D, la grille inclinée laisse un vide au-dessus : on le mesure une fois l'inclinaison finie et on le résorbe
  const scene = useRef(null);
  const [marge, setMarge] = useState(0);
  useLayoutEffect(() => {
    const el = scene.current;
    if (!el) return undefined;
    const grille = el.querySelector(".matrice");
    const mesurer = () => {
      if (!d3) { setMarge(0); return; }
      const haut = Math.min(...[...grille.children].map((c) => c.getBoundingClientRect().top));
      setMarge(Math.max(0, haut - el.getBoundingClientRect().top - 30));
    };
    mesurer();
    grille.addEventListener("transitionend", mesurer);
    window.addEventListener("resize", mesurer);
    return () => { grille.removeEventListener("transitionend", mesurer); window.removeEventListener("resize", mesurer); };
  }, [d3, matchups, mz, prof, down, dist]);
  if (!matchups) return <div className="squelette" aria-busy="true"><div /><div /><div /></div>;
  const lignes = matchups.filter((r) => (mz === "tous" || r.man_zone === mz) && (prof === "tous" || r.depth === prof)
    && (down === "tous" || String(r.down) === down) && (dist === "tous" || r.dist_bucket === dist));
  const total = agreger(lignes);
  const tranches = [...new Set(matchups.map((r) => r.dist_bucket))].sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
  const libTranche = (t) => (t.endsWith("+") ? `${t.slice(0, -1)} et +` : t.replace("-", " à "));
  const couvs = ORDRE_COUV.filter((c) => lignes.some((r) => r.coverage_type === c));
  const routes = ORDRE_ROUTES.filter((r) => lignes.some((l) => l.route === r));
  const cellule = (route, couv) => agreger(lignes.filter((l) => l.route === route && l.coverage_type === couv));
  return (
    <section>
      <h2 className="titre-ecran">Où le receveur finit ouvert</h2>
      <p className="note">Séparation à l'arrivée du ballon (yd) entre le receveur ciblé et le défenseur le plus proche au lancer, par route et par couverture. Ligue entière.</p>
      <div className="filtres-matrice">
        <div className="filtre"><span className="filtre-titre">Couverture</span>
          <Segment label="Couverture" valeur={mz} onChange={filtrer(setMz)} options={[["tous", "Man + zone"], ["Man", "Man"], ["Zone", "Zone"]]} /></div>
        <div className="filtre"><span className="filtre-titre">Profondeur de la passe</span>
          <Segment label="Profondeur" valeur={prof} onChange={filtrer(setProf)} options={[["tous", "Toutes"], ["short", <>Courtes<small>moins de 15 yd</small></>], ["deep", <>Profondes<small>15 yd et plus</small></>]]} /></div>
        <div className="filtre"><span className="filtre-titre">Down</span>
          <Segment label="Down" valeur={down} onChange={filtrer(setDown)} options={[["tous", <>Tous<small>downs</small></>], ["1", <>1er<small>down</small></>], ["2", <>2e<small>down</small></>], ["3", <>3e<small>down</small></>], ["4", <>4e<small>down</small></>]]} /></div>
        <div className="filtre"><span className="filtre-titre">Distance à gagner (yards to go)</span>
          <Segment label="Distance" valeur={dist} onChange={filtrer(setDist)} options={[["tous", <>Toutes<small>distances</small></>], ...tranches.map((t) => [t, <>{libTranche(t)}<small>yd à gagner</small></>])]} /></div>
      </div>
      {total && <p className="resume-matrice"><b>{total.n}</b> passes · séparation moyenne <b>{yd(total.sep)}</b> · {libSep(total.sep)}</p>}
      <div ref={scene} className={`heatmap-scene ${d3 ? "d3" : ""}`} style={{ marginTop: -marge }}>
        <div className="matrice" style={{ gridTemplateColumns: `62px repeat(${couvs.length}, minmax(0, 1fr))` }}>
          <span />
          {couvs.map((c) => <span key={c} className="hm-entete" title={c}>{ABR_COUV[c]}</span>)}
          {routes.map((r) => (
            <Fragment key={r}>
              <span className="hm-ligne">{r}</span>
              {couvs.map((c) => {
                const v = cellule(r, c);
                const ok = v && v.n >= SEUIL_N;
                const [fond, encre] = ok ? COUL_SEP[libSep(v.sep)] : ["#e6e5e0", "#52514e"];
                return (
                  <button key={c} className={`hm-case ${ok ? "" : "insuffisant"}`} style={{ background: fond, color: encre, "--h": ok ? `${4 + Math.min(v.sep, 6) * 4}px` : "0px" }}
                    onClick={() => v && setSel({ route: r, couv: c, v })} aria-label={v ? `${r} contre ${c} : ${yd(v.sep)}, ${v.n} passes` : `${r} contre ${c} : aucune passe`}>
                    {v ? (ok ? <b>{v.sep.toFixed(1)}</b> : <small>n={v.n}</small>) : ""}
                  </button>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <p className="legende-sep">
        {Object.entries(COUL_SEP).map(([lib, [f]]) => <span key={lib}><i style={{ background: f }} />{lib}</span>)}
      </p>
      <p className="note">C0 Cover-0 · C1 Cover-1 · 2M 2-Man · C2 Cover-2 · C3 Cover-3 · Q Quarters · C6 Cover-6 · PV Prevent. Contesté &lt; 1 yd, serré 1-2, ouvert 2-3, grand ouvert ≥ 3. Gris : échantillon insuffisant (n &lt; {SEUIL_N}). Courte : passe de moins de 15 yd. Touchez une case pour le détail.</p>
      {sel && (
        <div className="detail" role="dialog" aria-label="Détail de la situation">
          <button className="fermer" onClick={() => setSel(null)} aria-label="Fermer">✕</button>
          <h3>{sel.route} contre {sel.couv}</h3>
          {sel.v.n < SEUIL_N && <p className="alerte">Échantillon insuffisant : {sel.v.n} passes, ne pas conclure.</p>}
          <p className="detail-chiffre">{yd(sel.v.sep)} <span>{libSep(sel.v.sep)}</span></p>
          <p>Séparation à l'arrivée du ballon.</p>
          <p>Grand ouvert sur <b>{pct(sel.v.ouvert)}</b> des actions, contesté sur <b>{pct(sel.v.conteste)}</b>.</p>
          <p>Fenêtre passée de <b>{yd(sel.v.lancer)}</b> au lancer à <b>{yd(sel.v.sep)}</b> à l'arrivée.</p>
          {Number.isFinite(sel.v.epa) && <p>EPA moyen de l'attaque : <b>{sel.v.epa > 0 ? "+" : ""}{sel.v.epa.toFixed(2)}</b> point par passe.</p>}
          <p className="note">{sel.v.n} passes · fermeture moyenne {yd(sel.v.fermeture, true)}, IC 95 % [{sel.v.ic[0].toFixed(1)} ; {sel.v.ic[1].toFixed(1)}] yd {sel.v.icBoot ? "(bootstrap)" : "(approximation normale)"}</p>
        </div>
      )}
    </section>
  );
}

/** Classement des 32 défenses : logos posés sur une règle en yards, sans chevauchement. */
function EcranLigue({ abr, setAbr }) {
  const lignes = data.classement;
  const min = Math.min(...lignes.map((l) => l.fenetre)) - 0.05;
  const max = Math.max(...lignes.map((l) => l.fenetre)) + 0.05;
  const H = 860;
  const T = 44;
  const colonnes = 6;
  const yDe = (v) => ((max - v) / (max - min)) * H;
  const places = [];
  lignes.forEach((l) => {
    const y = yDe(l.fenetre);
    const ordre = [...Array(colonnes).keys()].sort((a, b) => Math.abs(a - (colonnes - 1) / 2) - Math.abs(b - (colonnes - 1) / 2));
    const col = ordre.find((c) => !places.some((p) => p.col === c && Math.abs(p.y - y) < T + 2)) ?? 0;
    places.push({ ...l, y, col });
  });
  const graduations = [];
  for (let v = Math.ceil(min * 10) / 10; v <= max; v += 0.1) graduations.push(Number(v.toFixed(1)));
  return (
    <section>
      <h2 className="titre-ecran">Les 32 défenses, fenêtre à l'arrivée</h2>
      <p className="note">En haut : les défenses qui laissent le plus d'air. En bas : celles qui referment le mieux. Touchez un logo pour l'analyser.</p>
      <div className="regle" style={{ height: H + T }}>
        {graduations.map((g) => (
          <div key={g} className="graduation" style={{ top: yDe(g) + T / 2 }}><span>{g.toFixed(1)}</span></div>
        ))}
        <div className="ligne-ligue" style={{ top: yDe(data.moy_ligue) + T / 2 }}><span>ligue {yd(data.moy_ligue)}</span></div>
        {places.map((p) => (
          <button key={p.defensive_team} className={`logo-regle ${p.defensive_team === abr ? "choisi" : ""}`}
            style={{ top: p.y, left: `calc(52px + ${p.col} * (100% - 60px) / ${colonnes})` }} onClick={() => setAbr(p.defensive_team)}
            aria-label={`${info(p.defensive_team).nom} : ${yd(p.fenetre)}`}>
            <Logo abr={p.defensive_team} taille={38} />
          </button>
        ))}
      </div>
    </section>
  );
}

function Segment({ valeur, options, onChange, label }) {
  return (
    <div className="segment" role="radiogroup" aria-label={label}>
      {options.map(([v, lib]) => (
        <button key={v} role="radio" aria-checked={valeur === v} className={valeur === v ? "actif" : ""} onClick={() => onChange(v)}>{lib}</button>
      ))}
    </div>
  );
}

function SelecteurEquipes({ abr, onChoix, onFermer }) {
  return (
    <div className="selecteur" role="dialog" aria-label="Choisir la défense adverse">
      <div className="selecteur-tete">
        <h2>Défense adverse</h2>
        {onFermer && <button className="fermer" onClick={onFermer} aria-label="Fermer">✕</button>}
      </div>
      <div className="grille-logos">
        {data.defenses.map((d) => (
          <button key={d} className={d === abr ? "choisi" : ""} onClick={() => onChoix(d)} aria-label={info(d).nom}>
            <Logo abr={d} taille={44} /><span>{d}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

const ICONES = {
  adversaire: <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12Zm0 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" />,
  manzone: <path d="M7 4a5 5 0 1 0 0 10A5 5 0 0 0 7 4Zm10 6a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z" />,
  matrice: <path d="M3 3h5v5H3zM10 3h5v5h-5zM17 3h4v5h-4zM3 10h5v5H3zM10 10h5v5h-5zM17 10h4v5h-4zM3 17h5v4H3zM10 17h5v4h-5zM17 17h4v4h-4z" />,
  ligue: <path d="M6 3h12v3a6 6 0 0 1-5 5.9V15h3v3H8v-3h3v-3.1A6 6 0 0 1 6 6V3Zm-4 1h3v2a3 3 0 0 1-3-2Zm17 0h3a3 3 0 0 1-3 2V4ZM7 20h10v2H7z" />,
};
const ONGLETS = [["adversaire", "Adversaire"], ["manzone", "Man/zone"], ["matrice", "Matrice"], ["ligue", "Ligue"]];

/** Vrai si la media query correspond (suit les changements de taille de fenêtre). */
function useMedia(requete) {
  const [ok, setOk] = useState(() => window.matchMedia(requete).matches);
  useEffect(() => {
    const m = window.matchMedia(requete);
    const suivre = () => setOk(m.matches);
    m.addEventListener("change", suivre);
    return () => m.removeEventListener("change", suivre);
  }, [requete]);
  return ok;
}

/** Ouverture : écran noir, logos NFL et AWS de part et d'autre, puis le noir s'ouvre en deux volets.
 *  Un toucher la passe ; mouvement réduit si le téléphone le demande. */
function Ouverture() {
  const [etat, setEtat] = useState("logos"); // logos -> ouvre -> fini
  useEffect(() => {
    const reduit = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const t1 = setTimeout(() => setEtat("ouvre"), reduit ? 500 : 1600);
    const t2 = setTimeout(() => setEtat("fini"), reduit ? 800 : 2700);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);
  if (etat === "fini") return null;
  return (
    <div className={`ouverture ${etat}`} aria-hidden="true" onClick={() => setEtat("fini")}>
      <div className="volet gauche"><img src="./marques/nfl.png" alt="" /></div>
      <div className="volet droite"><img src="./marques/aws-blanc.svg" alt="" /></div>
    </div>
  );
}

export default function App() {
  const [onglet, setOnglet] = useState("adversaire");
  const [abr, setAbr] = useState(data.defenses[0]);
  const [comparer, setComparer] = useState("");
  const [genre, setGenre] = useState("attaquer");
  const [contrat, setContrat] = useState({ matchups: null, plays: [] });
  // Fichiers du contrat d'équipe écrits par le pipeline Python (web/public/contrat/)
  useEffect(() => {
    Promise.all(["matchups", "play"].map((n) => fetch(`./contrat/${n}.json`).then((r) => (r.ok ? r.json() : null)).catch(() => null)))
      .then(([matchups, plays]) => setContrat({ matchups: matchups || [], plays: plays || [] }));
  }, []);
  const [d3, setD3] = useState(true);
  const [choix, setChoix] = useState(false);
  const e = info(abr);
  const cartes = useMemo(() => data.cartes.filter((c) => c.defensive_team === abr).sort((a, b) => a.rang - b.rang), [abr]);
  const cartesGenre = cartes.filter((c) => c.type === genre);
  const pc = useMedia("(min-width: 1100px)");
  const rendreCartes = (liste) => liste.length === 0
    ? <p className="info">Aucune route avec assez de passes dans ce sens pour cette défense.</p>
    : <div className="cartes">{liste.map((c) => <CarteRoute key={c.route} c={c} abr={abr} d3={d3} action={contrat.plays.find((p) => p.defensive_team === abr && p.route === c.route)} />)}</div>;

  return (
    <div className="app" style={{ "--equipe": e.couleur, "--equipe2": e.couleur2 }}>
      <div className="marques">
        <img src="./marques/nfl.png" alt="NFL" height="30" />
        <span>Big Data Bowl 2026</span>
        <img src="./marques/aws.svg" alt="AWS" height="22" />
      </div>
      <header className="bandeau">
        <button className="bandeau-equipe" onClick={() => setChoix(true)} aria-label="Changer de défense adverse">
          <span className="logo-cadre"><Logo abr={abr} taille={58} /></span>
          <span className="bandeau-texte">
            <small>Défense adverse · toucher pour changer</small>
            <strong>{e.nom}</strong>
          </span>
        </button>
        <div className="bandeau-pied">
          <span>Fenêtre de réception (yd)</span>
          <Segment valeur={d3 ? "3d" : "2d"} onChange={(v) => setD3(v === "3d")} label="Vue" options={[["2d", "2D"], ["3d", "3D"]]} />
        </div>
      </header>

      <nav className="nav-bas" role="tablist">
        {ONGLETS.map(([k, lib]) => (
          <button key={k} role="tab" aria-selected={onglet === k} className={onglet === k ? "actif" : ""} onClick={() => { setOnglet(k); window.scrollTo(0, 0); }}>
            <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">{ICONES[k]}</svg>
            <span>{lib}</span>
          </button>
        ))}
      </nav>

      <div className={`grille onglet-${onglet}`}>
        <aside className="panneau-gauche">
          <SelecteurEquipes abr={abr} onChoix={setAbr} />
          {onglet === "manzone" && (
            <div className="comparer">
              <label htmlFor="comparer">Comparer avec</label>
              <select id="comparer" value={comparer} onChange={(ev) => setComparer(ev.target.value)}>
                <option value="">— aucune —</option>
                {data.defenses.filter((d) => d !== abr).map((d) => <option key={d} value={d}>{info(d).nom}</option>)}
              </select>
            </div>
          )}
        </aside>

        <main>
          {onglet === "adversaire" && (
            <section>
              {pc ? (
                // PC : plan de match complet, les deux sens côte à côte
                ["attaquer", "eviter"].map((g) => (
                  <div key={g} className="groupe-cartes" style={{ "--accent": g === "attaquer" ? BLEU : ORANGE }}>
                    <h2 className="titre-groupe">{g === "attaquer" ? "Routes à attaquer" : "Routes à éviter"}</h2>
                    {rendreCartes(cartes.filter((c) => c.type === g))}
                  </div>
                ))
              ) : (
                <>
                  <Segment valeur={genre} onChange={setGenre} label="Sens" options={[["attaquer", "Routes à attaquer"], ["eviter", "Routes à éviter"]]} />
                  {rendreCartes(cartesGenre)}
                </>
              )}
              <ToutesRoutes abr={abr} />
              <p className="note">Chaque carte rejoue l'action réelle de cette défense la plus proche de sa moyenne sur la route : trajectoires mesurées du receveur ciblé (blanc) et du défenseur le plus proche au lancer (logo), ballon interpolé du passeur au point de chute. Cercle blanc : fenêtre de réception. Cercle jaune : moyenne de la ligue sur la route à l'arrivée. Confiance élevée si ≥ 50 passes et écart ≥ 0,5 yd ; moyenne si ≥ 30 et ≥ 0,3 ; faible sinon.</p>
            </section>
          )}
          {onglet === "manzone" && <EcranManZone abr={abr} comparer={comparer} d3={d3} />}
          {onglet === "matrice" && <EcranMatrice matchups={contrat.matchups} d3={d3} />}
          {onglet === "ligue" && (
            <>
              <EcranLigue abr={abr} setAbr={setAbr} />
            </>
          )}
          <footer className="source">Source : {data.source} · Données saison {data.saison} · seuls le receveur ciblé et les défenseurs proches du point de chute sont suivis pendant le vol. Logos : marques de la NFL et des clubs, usage d'identification.</footer>
        </main>

        <aside className="panneau-droit">
          <h2><Logo abr={abr} taille={30} /> Plan contre {e.surnom}</h2>
          {cartes.map((c) => (
            <div key={c.type + c.route} className="reco" style={{ "--accent": c.type === "attaquer" ? BLEU : ORANGE }}>
              <span className="reco-type">{c.type === "attaquer" ? "Attaquer" : "Éviter"}</span>
              <span className="reco-route">{c.route}</span>
              <span className="reco-chiffre">{yd(c.ecart_vs_ligue, true)}</span>
              <span className="reco-detail">{c.n_actions} passes · confiance {LIB_CONF[c.confiance]}</span>
            </div>
          ))}
        </aside>
      </div>

      <Ouverture />
      {choix && <SelecteurEquipes abr={abr} onChoix={(d) => { setAbr(d); setChoix(false); }} onFermer={() => setChoix(false)} />}
    </div>
  );
}
