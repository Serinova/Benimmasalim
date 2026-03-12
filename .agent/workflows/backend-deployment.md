---
description: How to deploy the backend to Google Cloud Production
---
// turbo-all
This workflow defines the safe, automated procedure to deploy the *Benim Masalım* backend to Google Cloud Run, ensuring the database proxy is tested and migrations are handled gracefully.

1. Navigate to the root level of the project.
// turbo
2. Verify that `deploy_production.sh` exists and is executable in the root directory.
// turbo
3. Set the required powershell environment variables for DB proxy access:
```powershell
$env:PYTHONIOENCODING="utf8"
$env:DATABASE_URL="postgresql+asyncpg://postgres:BnmMsl2026ProdDB%21@127.0.0.1:5433/benimmasalim"
```
// turbo
4. Ask the user for confirmation if there are any pending Alembic migrations in `backend/alembic/versions` that the user has NOT approved yet. If there are none, proceed.
// turbo
5. Run the deployment script `.\deploy_production.sh`. This process takes around 2-3 minutes to push images to Artifact Registry and deploy to Cloud Run.
// turbo
6. If the deployment script fails midway, capture the logs and execute `gcloud run services describe benimmasalim-backend --region europe-west1` to diagnose the deployment issue.
// turbo
7. Report the final Status URL or rollback instructions to the user.
