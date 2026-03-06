# Migration vers Cloudflare + Hono — Todo complet

## Architecture cible

```
GitHub Actions (cron 6h)
  └── python-jobspy scraper
        └── POST /jobs/sync → Cloudflare Worker (Hono)
                                    └── D1 (SQLite / Drizzle)
                                          ↑
                              Cloudflare Pages (Nuxt)
```

---

## 1. Prérequis

- [ ] Compte Cloudflare créé sur [cloudflare.com](https://cloudflare.com)
- [ ] Wrangler CLI installé : `npm install -g wrangler`
- [ ] Authentification : `wrangler login`
- [ ] Repo GitHub avec secrets configurés (étape 6)

---

## 2. Créer le Worker Hono

### Init du projet
- [ ] Créer le dossier `worker/` à la racine
- [ ] Initialiser :
  ```bash
  cd worker
  npm create hono@latest .
  # Sélectionner : cloudflare-workers
  npm install drizzle-orm
  npm install -D drizzle-kit wrangler
  ```

### Structure cible `worker/`
```
worker/
├── src/
│   ├── index.ts        # Hono app + routes
│   ├── schema.ts       # Drizzle schema
│   └── db.ts           # Drizzle client D1
├── drizzle.config.ts
├── wrangler.toml
└── package.json
```

---

## 3. Créer la base D1

- [ ] Créer la DB :
  ```bash
  wrangler d1 create jobboard-db
  ```
- [ ] Copier le `database_id` retourné dans `wrangler.toml` :
  ```toml
  name = "jobboard-worker"
  compatibility_date = "2024-01-01"
  main = "src/index.ts"

  [[d1_databases]]
  binding = "DB"
  database_name = "jobboard-db"
  database_id = "VOTRE_DATABASE_ID"
  ```

---

## 4. Drizzle schema + migrations

### `worker/src/schema.ts`
- [ ] Créer le schema équivalent à ta DB MySQL actuelle :
  ```typescript
  import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

  export const jobs = sqliteTable("jobs", {
    id: integer("id").primaryKey({ autoIncrement: true }),
    title: text("title").notNull(),
    description: text("description"),
    source: text("source"),
    url: text("url"),
    createdAt: integer("created_at", { mode: "timestamp" }),
  });
  ```

### `worker/drizzle.config.ts`
- [ ] Configurer pour D1 :
  ```typescript
  import { defineConfig } from "drizzle-kit";
  export default defineConfig({
    schema: "./src/schema.ts",
    out: "./migrations",
    dialect: "sqlite",
  });
  ```

### Générer et appliquer les migrations
- [ ] `npx drizzle-kit generate`
- [ ] Appliquer en local : `wrangler d1 execute jobboard-db --local --file=./migrations/*.sql`
- [ ] Appliquer en prod : `wrangler d1 execute jobboard-db --remote --file=./migrations/*.sql`

---

## 5. Réécrire l'API en Hono

### `worker/src/db.ts`
```typescript
import { drizzle } from "drizzle-orm/d1";
import * as schema from "./schema";

export function getDb(env: Env) {
  return drizzle(env.DB, { schema });
}
```

### `worker/src/index.ts`
- [ ] Réécrire les 2 endpoints de `main.py` :
  ```typescript
  import { Hono } from "hono";
  import { cors } from "hono/cors";
  import { getDb } from "./db";
  import { jobs } from "./schema";
  import { like, or } from "drizzle-orm";

  type Env = { DB: D1Database; SYNC_SECRET: string };

  const app = new Hono<{ Bindings: Env }>();

  app.use("*", cors());

  // GET /jobs
  app.get("/jobs", async (c) => {
    const db = getDb(c.env);
    const q = c.req.query("q")?.toLowerCase();
    const source = c.req.query("source");

    let query = db.select().from(jobs);
    if (q) {
      query = query.where(or(like(jobs.title, `%${q}%`), like(jobs.description, `%${q}%`)));
    }
    if (source) {
      query = query.where(eq(jobs.source, source));
    }

    const results = await query;
    return c.json({ count: results.length, jobs: results });
  });

  // POST /jobs/sync — appelé par GitHub Actions
  app.post("/jobs/sync", async (c) => {
    const secret = c.req.header("x-sync-secret");
    if (secret !== c.env.SYNC_SECRET) return c.json({ error: "Unauthorized" }, 401);

    const body = await c.req.json();
    const db = getDb(c.env);
    await db.insert(jobs).values(body.jobs).onConflictDoNothing();
    return c.json({ status: "ok", inserted: body.jobs.length });
  });

  export default app;
  ```

### Variable secrète
- [ ] Créer le secret dans Cloudflare :
  ```bash
  wrangler secret put SYNC_SECRET
  # Entrer une valeur aléatoire forte
  ```
- [ ] Noter cette valeur pour GitHub Actions (étape 6)

---

## 6. GitHub Actions — scraper Python cron

- [ ] Créer `.github/workflows/scrape.yml` :
  ```yaml
  name: Scrape Jobs

  on:
    schedule:
      - cron: "0 */6 * * *"
    workflow_dispatch:        # déclenchement manuel possible

  jobs:
    scrape:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - uses: actions/setup-python@v5
          with:
            python-version: "3.12"

        - name: Install dependencies
          run: pip install -r api/requirements.txt

        - name: Run scraper and push to Worker
          env:
            WORKER_URL: ${{ secrets.WORKER_URL }}
            SYNC_SECRET: ${{ secrets.SYNC_SECRET }}
          run: python api/scripts/github_scrape.py
  ```

- [ ] Créer `api/scripts/github_scrape.py` :
  ```python
  import os, requests
  from scraper import run_scrape  # retourne une liste de jobs

  jobs = run_scrape()             # adapter selon ta signature actuelle

  res = requests.post(
      f"{os.environ['WORKER_URL']}/jobs/sync",
      json={"jobs": jobs},
      headers={"x-sync-secret": os.environ["SYNC_SECRET"]},
  )
  print(res.status_code, res.json())
  ```

- [ ] Ajouter les secrets GitHub dans Settings → Secrets :
  - `WORKER_URL` → `https://jobboard-worker.VOTRE_SUBDOMAIN.workers.dev`
  - `SYNC_SECRET` → même valeur que le secret Wrangler

---

## 7. Déployer le Worker

- [ ] Build + deploy :
  ```bash
  cd worker
  wrangler deploy
  ```
- [ ] Tester : `curl https://jobboard-worker.SUBDOMAIN.workers.dev/jobs`

---

## 8. Migrer le frontend Nuxt vers Cloudflare Pages

- [ ] Dans `nuxt.config.ts`, ajouter le preset :
  ```typescript
  nitro: {
    preset: "cloudflare-pages",
  }
  ```
- [ ] Mettre à jour les variables d'environnement :
  ```
  NUXT_PUBLIC_API_URL=https://jobboard-worker.SUBDOMAIN.workers.dev
  NITRO_API_URL=https://jobboard-worker.SUBDOMAIN.workers.dev
  ```
- [ ] Dans le dashboard Cloudflare → **Pages** → **New Project** → connecter GitHub
- [ ] Config build :
  - Build command : `nuxt build`
  - Output directory : `.output/public`
- [ ] Ajouter les variables d'environnement dans l'interface Pages
- [ ] Deploy

---

## 9. Tests post-déploiement

- [ ] `GET /jobs` → `{"count": 0, "jobs": []}`
- [ ] Déclencher le scraper manuellement : GitHub Actions → **Run workflow**
- [ ] Vérifier l'insertion : `GET /jobs` → données présentes
- [ ] Tester le frontend sur l'URL Pages
- [ ] Vérifier le prochain cron dans l'onglet Actions

---

## 10. Comparatif vs Render

| | Render (todo précédent) | Cloudflare + Hono |
|---|---|---|
| **Réécriture** | Minimale (juste driver DB) | API complète en TS |
| **Cold start** | ~30s (free tier) | **Aucun** (Workers = edge) |
| **DB gratuite** | 90 jours puis payant | **Permanent** |
| **Scraper Python** | Dans Render (cron service) | GitHub Actions |
| **Complexité setup** | Faible | Moyenne |
| **Vendor lock-in** | Faible | Moyen (D1/Workers) |

> **Verdict :** Cloudflare est supérieur en performance et coût long terme. Render est supérieur en vélocité de déploiement initial.
