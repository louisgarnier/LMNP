#!/bin/bash

# Script de vérification du backend
# Vérifie que le backend est démarré et accessible

API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

echo "🔍 Vérification du backend sur ${API_URL}..."

# Vérifier si le backend répond
if curl -s -f "${API_URL}/api/bilan/calculate?years=2021" > /dev/null 2>&1; then
    echo "✅ Backend accessible sur ${API_URL}"
    exit 0
else
    echo "❌ Backend non accessible sur ${API_URL}"
    echo ""
    echo "💡 Pour démarrer le backend:"
    echo "   cd backend && python3 -m uvicorn api.main:app --reload --port 8000"
    exit 1
fi

