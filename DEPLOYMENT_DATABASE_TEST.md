# AI SafeHome Database Deployment Test

This checklist verifies that AI SafeHome can save anonymous room-check results to Supabase after deployment.

## Safety Rules

The deployed database must not store:

- Uploaded photos
- Names
- Addresses
- Ages
- Medical history
- Medication lists
- Insurance information
- Real patient photos
- Faces
- Mail
- Bills
- Medication bottles
- Medical documents

The database may store only anonymous room-check results.

---

## Streamlit Cloud Secrets Required

The deployed app needs these secrets:

```toml
APP_VERSION = "1.0"
AI_ANALYSIS_MODE = "fake"
DATABASE_ENABLED = "true"
SUPABASE_URL = "your_supabase_project_url_here"
SUPABASE_SERVICE_ROLE_KEY = "your_supabase_secret_or_service_role_key_here"
OPENAI_MODEL = "gpt-5.5"
OPENAI_API_KEY = "your_openai_key_here"