import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" : le build fonctionne ouvert depuis n'importe quel dossier ou hébergement statique
export default defineConfig({ plugins: [react()], base: "./" });
