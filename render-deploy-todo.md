# Deploy vers Render — Todo complet

## 1. Prérequis locaux

- [ ] Compte Render créé sur [render.com](https://render.com)
- [ ] Repo Git pushé sur GitHub (ou GitLab)
- [ ] Structure du projet confirmée :
  ```
  /
  ├── api/
  │   ├── Dockerfile
  │   ├── requirements.txt
  │   ├── main.py
  │   ├── database.py
  │   ├── scraper.py
  │   └── scheduler.py
  ├── frontend/
  │   └── Dockerfile
  └── render.yaml
  ```

---

## 2. Migration MySQL → PostgreSQL

### `api/requirements.txt`
- [ ] Supprimer `PyMySQL==1.1.1`
- [ ] Ajouter `psycopg2-binary==2.9.9`

### `api/database.py`
- [ ] Remplacer le préfixe d'URL :
  ```python
  # Avant
  DATABASE_URL = "mysql+pymysql://user:password@mysql:3306/jobboard_db"
  # Après
  DATABASE_URL = os.environ.get("DATABASE_URL")  # injecté par Render
  ```
- [ ] Vérifier que les types SQLAlchemy utilisés sont compatibles PostgreSQL (pas de `TINYINT`, etc.)

### Alembic
- [ ] Mettre à jour `alembic.ini` ou `env.py` pour lire `DATABASE_URL` depuis les variables d'environnement
- [ ] Générer une nouvelle migration si nécessaire : `alembic revision --autogenerate -m "postgres migration"`

---

## 3. Mise à jour docker-compose.yml (environnement local)

- [ ] Remplacer le service `mysql` par `postgres` :
  ```yaml
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: jobboard_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d jobboard_db"]
      interval: 5s
      timeout: 3s
      retries: 5
  ```
- [ ] Mettre à jour `DATABASE_URL` dans le service `api` :
  ```yaml
  DATABASE_URL=postgresql+psycopg2://user:password@postgres:5432/jobboard_db
  ```
- [ ] Renommer le volume `mysql-data` → `postgres-data`
- [ ] Tester en local : `docker compose up --build`

---

## 4. Refactor du scheduler (APScheduler → Render Cron)

- [ ] Supprimer `apscheduler` de `requirements.txt`
- [ ] Supprimer les imports et appels `scheduler.start()` / `scheduler.shutdown()` dans `main.py`
- [ ] Supprimer le fichier `scheduler.py`
- [ ] Vérifier que `POST /jobs/sync` fonctionne de façon autonome (il sera appelé par le Cron Render)
- [ ] S'assurer que `run_scrape()` est importable en standalone depuis un script :
  ```python
  # scripts/cron_scrape.py
  from scraper import run_scrape
  import asyncio
  asyncio.run(run_scrape())
  ```

---

## 5. Créer `render.yaml` à la racine

- [ ] Créer le fichier `/render.yaml` :
  ```yaml
  services:
    - type: web
      name: jobboard-api
      runtime: docker
      dockerfilePath: ./api/Dockerfile
      envVars:
        - key: DATABASE_URL
          fromDatabase:
            name: jobboard-db
            property: connectionString

    - type: web
      name: jobboard-frontend
      runtime: docker
      dockerfilePath: ./frontend/Dockerfile
      envVars:
        - key: NUXT_PUBLIC_API_URL
          value: https://jobboard-api.onrender.com
        - key: NITRO_API_URL
          value: https://jobboard-api.onrender.com

    - type: cron
      name: jobboard-scraper
      runtime: docker
      dockerfilePath: ./api/Dockerfile
      schedule: "0 */6 * * *"
      dockerCommand: python scripts/cron_scrape.py

  databases:
    - name: jobboard-db
      plan: free
      databaseName: jobboard_db
      user: jobboard_user
  ```

---

## 6. Déploiement sur Render

- [ ] Aller sur [dashboard.render.com](https://dashboard.render.com)
- [ ] **New** → **Blueprint** → connecter le repo GitHub
- [ ] Render détecte `render.yaml` automatiquement
- [ ] Vérifier les 3 services créés : `jobboard-api`, `jobboard-frontend`, `jobboard-scraper`
- [ ] Vérifier la base `jobboard-db` créée

---

## 7. Post-déploiement

- [ ] Récupérer l'URL de l'API dans le dashboard Render (`https://jobboard-api.onrender.com`)
- [ ] Mettre à jour manuellement `NUXT_PUBLIC_API_URL` si elle diffère
- [ ] Lancer les migrations Alembic manuellement via le Shell Render :
  ```bash
  alembic upgrade head
  ```
- [ ] Tester `GET https://jobboard-api.onrender.com/jobs` → doit retourner `{"count": 0, ...}`
- [ ] Déclencher un premier scrape manuellement :
  ```bash
  curl -X POST https://jobboard-api.onrender.com/jobs/sync
  ```
- [ ] Vérifier le Cron Job dans le dashboard (onglet **Cron Jobs** → logs)
- [ ] Tester le frontend sur l'URL Render

---

## 8. Limites free tier à surveiller

| Ressource | Limite | Impact |
|---|---|---|
| Web Services | Dort après 15min d'inactivité | Cold start ~30s sur le premier appel |
| PostgreSQL | Gratuit 90 jours | Migrer vers Supabase avant expiration |
| Cron Jobs | Gratuit, limité à 1/mois en free? | Vérifier le plan au moment du setup |
| Docker builds | 500 min/mois | Suffisant pour un petit projet |

> **Note PostgreSQL :** À J+80, migrer la DB vers [Supabase](https://supabase.com) (free permanent) et mettre à jour `DATABASE_URL` dans les variables d'environnement Render.
