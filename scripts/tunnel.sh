#!/usr/bin/env bash
# Expose le frontend local (localhost:3000) en HTTPS public via Cloudflare —
# nécessaire pour le retour de banque Enable Banking (qui refuse localhost en
# production). Cloudflare sert l'app directement, sans page d'avertissement.
#
# PRÉREQUIS (une seule fois) : brew install cloudflared   (aucun compte requis)
#
# USAGE : ./scripts/tunnel.sh
#   → affiche une adresse https://xxxx.trycloudflare.com
#
# ⚠️ L'adresse est TEMPORAIRE : elle change à chaque redémarrage du tunnel.
#    Au moment de connecter la banque, enregistre l'adresse affichée à la fois
#    chez Enable Banking (redirect URL) ET dans .env (ENABLE_BANKING_REDIRECT_URL),
#    identiques, en ajoutant le chemin :
#      https://xxxx.trycloudflare.com/dashboard/transactions?tab=parametres&eb_callback=1
#    Le retour de banque rebondit ensuite tout seul vers localhost
#    (garde-fou localBounceTarget dans ParametresScreen.tsx).
#
#    Besoin d'une adresse FIXE (pour ne pas ré-enregistrer tous les ~90 jours) ?
#    → Tailscale Funnel (gratuit, stable) : on le mettra en place si utile.

set -euo pipefail

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "❌ cloudflared introuvable. Installe-le : brew install cloudflared"
  exit 1
fi

echo "🚀 Tunnel HTTPS → http://localhost:3000"
echo "   Repère l'adresse https://xxxx.trycloudflare.com ci-dessous."
echo "   Laisse cette fenêtre ouverte pendant la connexion à ta banque."
echo "   Ctrl+C pour arrêter."
exec cloudflared tunnel --url http://localhost:3000 --no-autoupdate