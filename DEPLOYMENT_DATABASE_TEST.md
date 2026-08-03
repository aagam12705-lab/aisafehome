# AI SafeHome Saved-Check Deployment Test

Use this checklist after deploying the app with optional Supabase saving enabled.

## Required configuration

- [ ] `DATABASE_ENABLED=true`
- [ ] Supabase URL and service-role secret are configured as deployment secrets, never committed to GitHub.
- [ ] Real AI configuration is present only if real AI analysis is enabled.
- [ ] Optional email configuration is present only if server-side email is enabled.

## Account and saved-room checks

- [ ] A new account accepts a valid email address and password.
- [ ] The stored password is a hash, not a readable password.
- [ ] Password-reset email goes to the account email address.
- [ ] A signed-in person can create a Room Name and save a completed check.
- [ ] A person can still complete a check without signing in.
- [ ] Rechecking the same Room Name updates stats, trends, and before/after comparison.

## Data checks

- [ ] Saved rows contain only the account and room-check information described in [DATA_POLICY.md](DATA_POLICY.md).
- [ ] No uploaded photo or base64 image data appears in Supabase.
- [ ] No uploaded photo is included in email summaries.
- [ ] The app gives a helpful message if Supabase is unavailable.

## Deployment smoke test

- [ ] App loads on desktop and phone.
- [ ] Saving works when enabled and stays out of the way when disabled.
- [ ] Dark and high-contrast mode stay readable after deployment.
- [ ] No secret, API key, raw database error, or stack trace is shown to a normal user.
