# Commandes pour démarrer les serveurs

## Backend API (FastAPI)

### Terminal 1 - Backend
```bash
cd backend
python3 -m uvicorn api.main:app --reload --port 8000
```

Le serveur backend sera accessible sur : **http://localhost:8000**
- API : http://localhost:8000/api
- Documentation Swagger : http://localhost:8000/docs
- Health check : http://localhost:8000/health

---

## Frontend (Next.js)

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Le serveur frontend sera accessible sur : **http://localhost:3000**
- Dashboard : http://localhost:3000/dashboard

---

## Commandes rapides (depuis la racine du projet)

### Backend
```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/DEV/LMNP/backend" && python3 -m uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/DEV/LMNP/frontend" && npm run dev
```

---

## Vérification

Une fois les deux serveurs démarrés :

1. **Vérifier le backend** :
   ```bash
   curl http://localhost:8000/health
   ```
   Devrait retourner : `{"status":"healthy"}`

2. **Vérifier le frontend** :
   Ouvrir dans le navigateur : http://localhost:3000

---

## Arrêter les serveurs

- **Backend** : `Ctrl + C` dans le terminal backend
- **Frontend** : `Ctrl + C` dans le terminal frontend

---

## Notes

- Le backend doit être démarré avant le frontend pour que la connexion API fonctionne
- Le flag `--reload` active le rechargement automatique lors des modifications
- Le frontend redirige automatiquement vers `/dashboard`

