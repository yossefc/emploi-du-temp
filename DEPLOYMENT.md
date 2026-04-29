# Guide de déploiement — Firebase Hosting + Render

Architecture cible :
- **Frontend React/Vite** → Firebase Hosting (gratuit)
- **Backend FastAPI** → Render Web Service (free tier — Docker)
- **PostgreSQL** → Render PostgreSQL (free tier, expire à 90 j, à renouveler)
- **Redis** → Render Redis (free tier)

## Pré-requis

- Compte GitHub (pour pousser le code que Render va builder)
- Compte [Render](https://render.com) (gratuit, login via GitHub)
- Compte [Firebase](https://console.firebase.google.com) (gratuit)
- Node.js 18+ et `npm` installés
- Firebase CLI : `npm install -g firebase-tools`
- Git installé

## Étape 0 — Sécuriser les secrets avant de pousser

```bash
cd "C:/Users/USER/Desktop/emploi du temp/emploi-du-temp"

# Retirer .env du suivi git s'il y était
git rm --cached .env .env.backup .env.new 2>/dev/null || true

git add .gitignore
git commit -m "chore: ignore secrets and build artefacts"
```

Vérifie que `.env` n'est plus tracké : `git ls-files | grep -E "\.env$"` doit ne rien afficher.

## Étape 1 — Pousser le code sur GitHub

```bash
# Si pas encore initialisé
git init
git add .
git commit -m "initial commit"
git branch -M main

# Crée un repo vide sur github.com puis :
git remote add origin https://github.com/<ton-user>/emploi-du-temps.git
git push -u origin main
```

## Étape 2 — Déployer le backend sur Render

1. Va sur https://dashboard.render.com → **New** → **Blueprint**
2. Connecte ton repo GitHub
3. Render détecte automatiquement [render.yaml](render.yaml) à la racine
4. Clique **Apply** : il crée 3 services :
   - `emploi-du-temp-backend` (web)
   - `emploi-du-temp-db` (PostgreSQL)
   - `emploi-du-temp-redis` (Redis)
5. **Configure les variables manquantes** sur la page du service backend → onglet **Environment** :
   - `CORS_ORIGINS` → mets ton domaine Firebase (sera connu après l'étape 3) — pour l'instant : `https://*.web.app,https://*.firebaseapp.com`
   - `ANTHROPIC_API_KEY` → ta vraie clé Anthropic
   - `OPENAI_API_KEY` → ta vraie clé OpenAI (optionnel)
6. Clique **Manual Deploy** → **Deploy latest commit**
7. Attends ~5-10 min. L'URL sera : `https://emploi-du-temp-backend.onrender.com`
8. Vérifie : `https://emploi-du-temp-backend.onrender.com/health` doit renvoyer `{"status": "healthy", ...}`

> ⚠️ **Free tier Render** : le backend s'endort après 15 min d'inactivité. Le premier appel après veille met 30-60 s à répondre.

### Initialiser la base de données

L'app appelle `Base.metadata.create_all` au démarrage, donc les tables sont créées automatiquement au premier boot. Pour seeder un utilisateur admin :

Render → service backend → **Shell** :
```bash
python -c "
from app.db.base import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash
db = SessionLocal()
admin = User(username='admin', email='admin@local', hashed_password=get_password_hash('changeme'), full_name='Admin', role='admin', is_active=True)
db.add(admin); db.commit()
print('admin créé')
"
```

**Change le mot de passe `changeme` immédiatement après le premier login.**

## Étape 3 — Déployer le frontend sur Firebase Hosting

```bash
cd frontend

# 1. Login Firebase
firebase login

# 2. Crée un projet sur https://console.firebase.google.com (ex: "emploi-du-temp-prod")
#    puis remplace REMPLACE_PAR_TON_PROJECT_ID dans .firebaserc par l'ID du projet
```

Édite [.firebaserc](frontend/.firebaserc) et mets ton vrai project ID.

```bash
# 3. Met à jour l'URL backend dans .env.production
#    Édite frontend/.env.production avec l'URL Render obtenue à l'étape 2
```

Édite [.env.production](frontend/.env.production) :
```
VITE_API_BASE_URL=https://emploi-du-temp-backend.onrender.com
```

```bash
# 4. Installe et build
npm install
npm run build

# 5. Déploie
firebase deploy --only hosting
```

Firebase affichera l'URL de prod : `https://<project-id>.web.app`

## Étape 4 — Mettre à jour CORS sur le backend

Reviens sur Render → service backend → **Environment** :
- `CORS_ORIGINS` = `https://<project-id>.web.app,https://<project-id>.firebaseapp.com`
- Sauvegarde → le service redémarre automatiquement.

## Étape 5 — Tester

1. Ouvre `https://<project-id>.web.app`
2. Tu dois être redirigé vers `/login`
3. Login avec `admin` / le mot de passe défini à l'étape 2.
4. Vérifie que les pages chargent (dashboard, teachers, etc.).

## Mises à jour ultérieures

**Backend** : `git push` sur `main` → Render redéploie automatiquement.

**Frontend** :
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

## Coûts

| Service | Free tier | Si ça dépasse |
|---|---|---|
| Render web | 750 h/mois (assez) | 7 $/mois pour rester réveillé |
| Render Postgres | 1 Go, **expire à 90 j** | 7 $/mois |
| Render Redis | 25 Mo | 10 $/mois |
| Firebase Hosting | 10 Go transfert / mois | quasi-gratuit ensuite |

Total free : **0 €**. Si tu veux que le backend ne dorme jamais : **~14 $/mois**.

## Limites connues sur free tier

- Backend s'endort après 15 min d'inactivité (réveil ~30-60 s).
- Postgres expire à 90 j sur free tier — il faut migrer / recréer avant.
- Redis n'est PAS persistant en free tier.
- Génération d'emploi du temps lourde : peut timeout (Render coupe à 100 s sur free). Pour les gros calculs, passer Celery + Render Background Worker (payant) ou Cloud Run.

## Dépannage

**Backend renvoie 500 au démarrage** : check les logs Render. Cause fréquente : `DATABASE_URL` mal formée. Render fournit `postgres://`, mais SQLAlchemy 2.0 préfère `postgresql://`. Si erreur, va dans Environment et remplace le préfixe.

**CORS error sur le frontend** : vérifie que `CORS_ORIGINS` côté backend contient bien le domaine Firebase exact (https inclus, sans `/` final).

**Login échoue** : vérifie que `/auth/me` répond bien quand on appelle avec le token. Les tokens sont dans `localStorage` du navigateur.

**Page blanche après deploy Firebase** : le build est dans `frontend/dist/`. Vérifie que `firebase.json` pointe bien sur `dist`.
