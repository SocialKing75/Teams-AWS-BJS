"""
Vidéo de démo en motion design (1920×1080, MP4) : l'app React tourne dans un téléphone,
le script la pilote comme un coach (toucher, onglets, filtres) et affiche à côté les
métriques lues dans l'app au moment même. Aucun chiffre n'est écrit en dur : ils viennent
du DOM de l'app, de web/src/data.json et de outputs/rapport_verification.md.

    cd web && npm run dev            # l'app doit tourner
    python video/enregistrer_demo.py --app http://localhost:5173/ --sortie outputs/demo_app.mp4

Enregistrement : capture d'écran image par image de Chrome (CDP screencast), puis ffmpeg (H.264, 30 i/s).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parent.parent
CHAPITRES = ["Adversaire", "Route à attaquer", "Vue 3D", "Route à éviter", "Man / zone", "Matrice", "Ligue"]
BLEU, ORANGE = "#5aa2f0", "#f08a5d"   # versions éclaircies de la palette de l'app, lisibles sur fond sombre


def lire_verifications(chemin: Path) -> list[str]:
    """Phrases de vérification tirées du rapport du pipeline (rien si le rapport manque)."""
    if not chemin.exists():
        return []
    t = chemin.read_text(encoding="utf-8")
    lignes = []
    if m := re.search(r"recalcul numpy sur (\d+) actions.*?: ([\d.e+-]+) yard", t):
        lignes.append(f"Recalcul indépendant sur {m[1]} actions : écart max {m[2]} yard")
    if m := re.search(r"Case la plus fermée \((.+?)\) recalculée par boucle Python : n = (\d+)", t):
        lignes.append(f"Case {m[1]} recalculée par une boucle Python : n = {m[2]}, identique")
    if m := re.search(r"Stabilité.*?corrélation de rang ([\d.]+)", t):
        lignes.append(f"Stabilité entre les deux moitiés de saison : corrélation de rang {m[1]}")
    return lignes


def choisir_equipe(data: dict) -> str:
    """Défense de la démo : la carte « à attaquer » la plus marquée parmi celles de confiance élevée."""
    cartes = [c for c in data["cartes"] if c["type"] == "attaquer"]
    sures = [c for c in cartes if c["confiance"] == "elevee"] or cartes
    return max(sures, key=lambda c: c["ecart_vs_ligue"])["defensive_team"]


async def main():
    p = argparse.ArgumentParser(description="Vidéo de démo de l'app coach")
    p.add_argument("--app", default="http://localhost:5173/", help="URL de l'app React en cours d'exécution")
    p.add_argument("--sortie", default=str(RACINE / "outputs" / "demo_app.mp4"))
    p.add_argument("--fps", type=int, default=30)
    a = p.parse_args()

    data = json.loads((RACINE / "web" / "src" / "data.json").read_text(encoding="utf-8"))
    verifs = lire_verifications(RACINE / "outputs" / "rapport_verification.md")
    abr = choisir_equipe(data)
    equipe = data["equipes_info"][abr]
    images = Path(tempfile.mkdtemp(prefix="demo_images_"))
    horodatage: list[tuple[float, Path]] = []

    async with async_playwright() as pw:
        navigateur = await pw.chromium.launch()
        ctx = await navigateur.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = await ctx.new_page()
        await page.goto((RACINE / "video" / "studio.html").as_uri() + "?app=" + a.app)
        app = await (await page.wait_for_selector("#app")).content_frame()
        await app.wait_for_selector(".carte")
        await app.evaluate("document.fonts.ready")
        await page.evaluate("document.fonts.ready")

        attendre = page.wait_for_timeout
        studio = lambda js, arg=None: page.evaluate(f"(a) => studio.{js}", arg)
        await page.evaluate("addEventListener('scroll', () => scrollTo(0, 0))")
        ecran = await page.locator(".ecran").bounding_box()

        def borne(b):
            """Limite un rectangle à l'écran du téléphone."""
            x0, y0 = max(b["x"], ecran["x"] + 6), max(b["y"], ecran["y"] + 6)
            x1, y1 = min(b["x"] + b["width"], ecran["x"] + ecran["width"] - 6), min(b["y"] + b["height"], ecran["y"] + ecran["height"] - 6)
            return {"x": x0, "y": y0, "width": max(0, x1 - x0), "height": max(0, y1 - y0)}

        async def toucher(loc, pause=200):
            await loc.scroll_into_view_if_needed()
            b = await loc.bounding_box()
            await studio("toucher(a[0], a[1])", [b["x"] + b["width"] / 2, b["y"] + b["height"] / 2])
            await attendre(pause)
            await loc.click()

        async def cadre(loc, marge=8):
            await studio("cadre(a[0], a[1])", [borne(await loc.bounding_box()), marge])

        async def texte(loc):
            return (await loc.inner_text()).strip()

        async def chiffre_carte():
            """Route, écart vs ligue et textes de la première carte affichée."""
            carte = app.locator(".carte").first
            return {
                "route": await texte(carte.locator(".carte-route")),
                "ecart": await carte.locator(".carte-chiffre").evaluate("e => e.firstChild.textContent.trim()"),
                "phrase": await texte(carte.locator(".carte-action b")) if await carte.locator(".carte-action b").count() else "",
                "detail": await texte(carte.locator(".carte-detail").first),
            }

        def chapitre(i, duree):
            return studio("progression(a[0], a[1], a[2])", [CHAPITRES, i, duree])

        await app.wait_for_selector(".ouverture", state="detached", timeout=15000)

        # --- Enregistrement ---
        cdp = await ctx.new_cdp_session(page)

        async def sur_image(ev):
            f = images / f"{len(horodatage):06d}.jpg"
            f.write_bytes(base64.b64decode(ev["data"]))
            horodatage.append((ev["metadata"]["timestamp"], f))
            try:
                await cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", lambda ev: asyncio.ensure_future(sur_image(ev)))
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1})

        # 0. Intro
        await studio("saison(a)", data["saison"])
        n_passes = f"{data['n_passes']:,}".replace(",", " ")
        await studio("plein('intro', a)", f"""
            <div class="surtitre">Outil coach · bord de terrain · Données {data['saison']}</div>
            <h1>La fenêtre<br><em>de réception</em></h1>
            <div class="question">Entre le lancer et l'arrivée du ballon, qui referme la fenêtre de réception, et comment ?</div>
            <div class="rangee"><div>{n_passes}<small>passes suivies image par image</small></div>
              <div>{len(data['defenses'])}<small>défenses analysées</small></div>
              <div>{str(data['moy_ligue']).replace('.', ',')} yd<small>fenêtre moyenne à l'arrivée, ligue</small></div></div>""")
        await attendre(5200)
        # Le téléphone entre et l'app se recharge : l'ouverture NFL / AWS se joue à l'écran
        await app.goto(a.app)
        await app.wait_for_selector(".ouverture")
        await studio("plein('intro', null)")
        await studio("telephone(true)")
        await app.wait_for_selector(".carte")
        await app.evaluate("document.querySelector('.bandeau-pied .segment button').click()")   # vue 2D sous les volets
        await app.wait_for_selector(".ouverture", state="detached", timeout=15000)
        await attendre(500)

        # 1. Choisir l'adversaire
        await chapitre(0, 6)
        await studio("legende(a)", {"etape": 1, "total": len(CHAPITRES), "titre": "Choisir l'adversaire",
                                    "texte": f"Un toucher sur le bandeau : les <b>{len(data['defenses'])} défenses</b> de la saison, par logo. Utilisable d'une main."})
        await attendre(1400)
        await toucher(app.locator(".bandeau-equipe"))
        await attendre(1000)
        bouton = app.locator(f'.app > .selecteur .grille-logos button[aria-label="{equipe["nom"]}"]')
        await cadre(bouton)
        await attendre(900)
        await toucher(bouton)
        await studio("cadre(null)")
        await studio("couleur(a)", equipe["couleur"])
        await attendre(1600)

        # 2. Route à attaquer : carte avec l'action réelle rejouée
        c = await chiffre_carte()
        await chapitre(1, 7)
        await studio("legende(a)", {"etape": 2, "total": len(CHAPITRES), "titre": f"{c['route']} à attaquer", "chiffre": c["ecart"], "couleur": BLEU,
                                    "texte": f"de fenêtre en plus que la moyenne de la ligue sur cette route, face à <b>{equipe['nom']}</b>.<br>{c['detail']}",
                                    "source": f"Action réelle rejouée : {c['phrase']}" if c["phrase"] else None})
        await cadre(app.locator(".carte .terrain").first, 4)
        await attendre(7000)

        # 3. Vue 3D
        await chapitre(2, 5)
        await studio("cadre(null)")
        await studio("legende(a)", {"etape": 3, "total": len(CHAPITRES), "titre": "Caméra 3D",
                                    "texte": "La même action vue depuis la ligne de touche. Blanc : receveur ciblé. Logo : défenseur le plus proche au lancer. "
                                             "Disque blanc : fenêtre de réception. Cercle jaune : moyenne de la ligue."})
        await toucher(app.locator(".bandeau-pied .segment button").nth(1))
        await attendre(1200)
        await cadre(app.locator(".carte .terrain").first, 4)
        await attendre(4600)

        # 4. Route à éviter
        await chapitre(3, 6)
        await studio("cadre(null)")
        await toucher(app.locator(".segment button", has_text="Routes à éviter"))
        await attendre(500)
        c = await chiffre_carte()
        await studio("legende(a)", {"etape": 4, "total": len(CHAPITRES), "titre": f"{c['route']} à éviter", "chiffre": c["ecart"], "couleur": ORANGE,
                                    "texte": f"de fenêtre par rapport à la ligue : cette défense referme mieux la route.<br>{c['detail']}",
                                    "source": f"Action réelle rejouée : {c['phrase']}" if c["phrase"] else None})
        await cadre(app.locator(".carte .terrain").first, 4)
        await attendre(6000)

        # 5. Man / zone : la case la plus fermée de cette défense
        await chapitre(4, 6)
        await studio("cadre(null)")
        await toucher(app.locator(".nav-bas button").nth(1))
        await app.wait_for_selector(".cible .cible-chiffre")
        await attendre(900)
        cibles = []
        for i in range(await app.locator(".cible").count()):
            fig = app.locator(".cible").nth(i)
            v = await texte(fig.locator(".cible-chiffre"))
            if m := re.match(r"([\d.]+)", v):
                spans = await fig.locator("figcaption span").all_inner_texts()
                cibles.append((float(m[1]), i, await texte(fig.locator("figcaption b")), v, spans))
        _, i, titre, v, spans = min(cibles)
        fig = app.locator(".cible").nth(i)
        await fig.scroll_into_view_if_needed()
        await attendre(400)
        await studio("legende(a)", {"etape": 5, "total": len(CHAPITRES), "titre": f"{titre}", "chiffre": v, "couleur": "#fff",
                                    "texte": f"Sa couverture la plus serrée à l'arrivée du ballon. {' · '.join(s for s in spans[1:])}."
                                             f"<br>Tirets : fenêtre au lancer. Cercle jaune : ligue."})
        await cadre(fig, 6)
        await attendre(6000)

        # 6. Matrice ligue : route × couverture, filtrée sur les passes profondes
        await chapitre(5, 9)
        await studio("cadre(null)")
        await toucher(app.locator(".nav-bas button").nth(2))
        await attendre(700)
        await toucher(app.locator(".bandeau-pied .segment button").first)   # 2D pour lire les cases
        await attendre(500)
        await toucher(app.locator(".segment button", has_text="Profondes"))
        await attendre(600)
        resume = await texte(app.locator(".resume-matrice"))
        await studio("legende(a)", {"etape": 6, "total": len(CHAPITRES), "titre": "La matrice de la ligue",
                                    "texte": f"Séparation à l'arrivée par route et par couverture, re-calculée à chaque filtre (Σ somme / Σ n).<br><b>Passes profondes</b> : {resume}.",
                                    "source": "Gris : moins de 10 passes, on ne conclut pas."})
        grille = app.locator(".matrice")
        await grille.scroll_into_view_if_needed()
        await cadre(grille, 6)
        await attendre(3600)
        cases = []
        for lib in await app.locator(".hm-case:not(.insuffisant)").evaluate_all("l => l.map(e => e.getAttribute('aria-label'))"):
            if m := re.match(r"(.+?) contre (.+?) : ([\d.]+) yd, (\d+) passes", lib or ""):
                cases.append((float(m[3]), lib, m))
        _, lib, m = min(cases)
        await studio("cadre(null)")
        await toucher(app.locator(f'.hm-case[aria-label="{lib}"]'))
        await attendre(700)
        detail = app.locator(".detail")
        note = await texte(detail.locator("p.note"))
        etiquette = await texte(detail.locator(".detail-chiffre span"))
        await studio("legende(a)", {"etape": 6, "total": len(CHAPITRES), "titre": f"{m[1]} contre {m[2]}", "chiffre": f"{m[3]} yd", "couleur": ORANGE,
                                    "texte": f"<b>{etiquette}</b> : la case profonde la plus fermée de la ligue.<br>{note}"})
        await cadre(detail, 0)
        await attendre(5600)
        await studio("cadre(null)")
        await toucher(detail.locator(".fermer"))

        # 7. Ligue : où se situe la défense choisie
        await chapitre(6, 6)
        await toucher(app.locator(".nav-bas button").nth(3))
        await attendre(800)
        classement = sorted(data["classement"], key=lambda l: l["fenetre"])
        rang = next(k for k, l in enumerate(classement, 1) if l["defensive_team"] == abr)
        ligne = classement[rang - 1]
        logo = app.locator(".logo-regle.choisi")
        await logo.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'center'})")
        await attendre(900)
        await studio("legende(a)", {"etape": 7, "total": len(CHAPITRES), "titre": f"{equipe['nom']} dans la ligue", "chiffre": f"{rang}e", "couleur": "#fff",
                                    "texte": f"sur {len(classement)} défenses pour refermer la fenêtre : <b>{ligne['fenetre']} yd</b> à l'arrivée en moyenne "
                                             f"(ligue {data['moy_ligue']} yd, {ligne['n']} passes). 1er = la défense qui referme le mieux."})
        await cadre(logo, 8)
        await attendre(6000)

        # 8. Conclusion
        await studio("cadre(null)")
        await studio("progression(a[0], a[1], a[2])", [CHAPITRES, -1, 1])
        await studio("telephone(false)")
        await page.evaluate("document.getElementById('legende').className = 'legende sort'")
        liste = "".join(f"<p>{l}</p>" for l in verifs)
        await studio("plein('outro', a)", f"""
            <div class="surtitre">Données {data['saison']} · chaque chiffre vérifié deux fois</div>
            <h1>Une information<br><em>par écran</em></h1>
            <div class="liste">{liste}</div>
            <div class="marques-fin"><div class="pastille"><img src="../web/public/marques/nfl.png" alt="NFL" height="70"><img src="../web/public/marques/aws.svg" alt="AWS" height="48"></div>
              <div class="question">{data['source']}</div></div>""")
        await attendre(6500)

        await cdp.send("Page.stopScreencast")
        await attendre(300)
        await navigateur.close()

    # --- Montage : images horodatées -> vidéo à cadence fixe ---
    horodatage.sort()
    liste = images / "liste.txt"
    with liste.open("w", encoding="utf-8") as f:
        for (t, img), (t2, _) in zip(horodatage, horodatage[1:] + [(horodatage[-1][0] + 1 / a.fps, None)]):
            f.write(f"file '{img.as_posix()}'\nduration {max(t2 - t, 0.001):.4f}\n")
        f.write(f"file '{horodatage[-1][1].as_posix()}'\n")
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
                    "-vf", f"fps={a.fps},scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-movflags", "+faststart", a.sortie], check=True)
    duree = horodatage[-1][0] - horodatage[0][0]
    print(f"{len(horodatage)} images capturées sur {duree:.1f} s -> {a.sortie} ({os.path.getsize(a.sortie) / 1e6:.1f} Mo)")
    print(f"Défense de la démo : {equipe['nom']} ({abr})")
    shutil.rmtree(images, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
