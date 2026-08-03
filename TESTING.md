# AI SafeHome Testing Guide

Test only with staged, non-patient room photos. Do not use photos containing faces, addresses, mail, medicine bottles, or medical documents.

## Core check flow

- [ ] Landing page explains the four-step flow in plain language.
- [ ] Room selection works on desktop and phone.
- [ ] One JPG, PNG, or WEBP room photo up to 30 MB uploads correctly.
- [ ] The preview is upright and the photo-quality message is understandable.
- [ ] AI results show readable hazard cards and approximate numbered photo markers.
- [ ] Follow-up questions are generated only for uncertainty and use simple language.
- [ ] Risk score stays between 0 and 100 and shows a risk label and color bar.
- [ ] The three-step safety plan appears while remaining recommendations are available under “See more suggested steps.”
- [ ] The full report downloads and Read Aloud works when enabled.

## Saved-room flow

- [ ] A person can continue without signing in.
- [ ] A valid email and password can create an optional account.
- [ ] Password-reset code goes only to the account email.
- [ ] A Room Name can be created or an existing Room Name selected.
- [ ] Saving a check adds it to room stats.
- [ ] A recheck appears in score trends and before/after comparison.
- [ ] Before/after labels show readable times, score, and risk label without exposing check IDs.

## Sharing

- [ ] Email summary accepts one to five recipient email addresses.
- [ ] Removing a recipient keeps at least one email field available.
- [ ] Download and email text do not include uploaded photos.

## Accessibility and mobile

- [ ] Test Standard, Large, and Extra Large text.
- [ ] Test Light, Dark, System, and High Contrast modes.
- [ ] Verify fields, tooltips, accessibility controls, and dropdowns remain readable in every mode.
- [ ] Verify the app works without horizontal scrolling on a narrow phone screen.
- [ ] Verify controls are comfortably tappable and keyboard reachable.
- [ ] Verify Read Aloud buttons can be enabled and disabled in Accessibility.

## Responsible-AI checks

- [ ] Sample/fallback results are clearly labeled as sample results.
- [ ] The privacy and AI information panel is visible from the landing page.
- [ ] Photo upload warns people not to upload personal information.
- [ ] The app does not claim to diagnose medical conditions or guarantee fall prevention.
- [ ] A failed AI call shows a safe fallback rather than crashing.
