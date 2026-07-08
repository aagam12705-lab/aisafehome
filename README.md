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