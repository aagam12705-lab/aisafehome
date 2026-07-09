# AI SafeHome

AI SafeHome is a beginner-friendly Python Streamlit web app for the Congressional App Challenge.

The app helps older adults, families, and caregivers identify possible home fall hazards from a room photo and checklist, then creates a plain-English safety report.

## Version 1 Goal

Version 1 will run as a mobile-friendly Streamlit web app that can open in Safari on iPhone.

This is not a native iOS app yet.

## MVP Features

- Landing page
- Room selection
- Upload or take a room photo
- Photo preview
- AI-style hazard results
- Checklist
- Fall-risk score from 0 to 100
- Low / Moderate / High risk label
- Plain-English recommendations
- Printable safety report
- Safety disclaimer

## Privacy and Safety Rules

AI SafeHome does not collect:

- Names
- Addresses
- Age
- Medical history
- Medications
- Real patient photos

The app does not diagnose medical risk, does not guarantee fall prevention, and does not replace a qualified professional.

## Tech Stack

- Python
- Streamlit
- Pillow
- python-dotenv
- OpenAI API later
- GitHub
- Streamlit Community Cloud or Render

## How to Run Locally

```bash
source venv/bin/activate
streamlit run app.py

## Deployment

This app is designed to deploy on Streamlit Community Cloud.

Main file:

```text
app.py

## Final Demo Materials

This project includes:

- `TESTING.md` — testing checklist
- `DEMO_SCRIPT.md` — 2–3 minute demo video script
- `SUBMISSION_NOTES.md` — app explanation and judging alignment
- `FINAL_CHECKLIST.md` — final readiness checklist
- `sample_photos/README.md` — staged photo rules

## AI Use Disclosure

AI SafeHome uses AI to help identify possible visible environmental fall hazards from room photos.

AI may make mistakes. Users should review the room themselves and ask a qualified professional for serious safety concerns.

AI coding tools were also used for brainstorming, debugging, and improving the project. The student reviewed, modified, tested, and can explain the code.

## Final Safety Statement

AI SafeHome is an educational home-safety tool.

It does not diagnose medical conditions, predict individual medical fall risk, or guarantee fall prevention.

It does not replace a doctor, therapist, or home-safety professional.

Use staged, non-patient photos only.