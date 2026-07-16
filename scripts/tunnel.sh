#!/usr/bin/env bash
# Lance le tunnel ngrok qui expose le frontend local (localhost:3000) en HTTPS
# public — nécessaire pour le retour de banque Enable Banking (qui refuse
# localhost en production).
#
# PRÉREQUIS (une seule fois) :
#   1. brew install ngrok
#   2. créer un compte gratuit sur https://ngrok.com
#   3. ngrok config add-authtoken <TON_TOKEN>       (garde ton token privé)
#   4. réclamer ton domaine fixe gratuit dans le dashboard ngrok (Domains)
#
# USAGE :
#   EB_DOMAIN=lmnp-louis.ngrok-free.app ./scripts/tunnel.sh
# ou renseigne EB_DOMAIN plus bas.

set -euo pipefail

EB_DOMAIN="${EB_DOMAIN:-}"

if [[ -z "$EB_DOMAIN" ]]; then
  echo "❌ EB_DOMAIN non défini."
  echo "   Exemple : EB_DOMAIN=lmnp-louis.ngrok-free.app ./scripts/tunnel.sh"
  exit 1
fi

if ! command -v ngrok >/dev/null 2>&1; then
  echo "❌ ngrok introuvable. Installe-le : brew install ngrok"
  exit 1
fi

echo "🚀 Tunnel HTTPS → http://localhost:3000"
echo "   Adresse publique : https://${EB_DOMAIN}"
echo "   (À enregistrer chez Enable Banking + dans .env, identique.)"
echo "   Ctrl+C pour arrêter."
exec ngrok http 3000 --domain="${EB_DOMAIN}"
