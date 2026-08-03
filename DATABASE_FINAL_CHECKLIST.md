# AI SafeHome Saved-Check Checklist

## Setup

- [ ] Supabase tables for accounts, Room Names, checks, and check details exist.
- [ ] Local environment files are excluded from Git.
- [ ] Deployment secrets are configured.
- [ ] The app works normally when saved checks are disabled.

## Stored information

- [ ] Account email address
- [ ] Secure password hash
- [ ] Room Name and room type
- [ ] Score, risk label, hazards, recommendations, and follow-up answers
- [ ] Check time and analysis mode

## Information not stored in the app database

- [ ] Uploaded photos or base64 image data
- [ ] Medical history, medication information, insurance, or patient IDs
- [ ] Home street address or GPS location

## Behavior

- [ ] People may use the app without an account.
- [ ] People must sign in before saving a check.
- [ ] A saved check appears in the correct Room Name history.
- [ ] Before/after comparison and trends use saved checks from that Room Name.
- [ ] Users see a simple helpful message if saving fails.
