# AI SafeHome Demo Script

Target length: 2–3 minutes.

## Opening

Hi, my name is Aagam, and I built AI SafeHome for the Congressional App Challenge.

Falls are a major concern for older adults, and many hazards are simple things inside the home, such as loose rugs, cords, clutter, poor lighting, stairs, and bathroom risks.

## Problem

Families often do not know what to look for until someone gets hurt. I wanted to build a simple tool that helps older adults and caregivers notice possible home hazards earlier.

## App Overview

AI SafeHome is a web app built with Python and Streamlit.

The user selects a room, uploads a staged room photo, answers a short checklist, and gets a plain-English safety report.

## Demo Step 1 — Room Selection

First, I choose the room type. In this example, I will choose Living Room.

## Demo Step 2 — Photo Upload

Next, I upload a staged room photo. The app shows a preview and reminds users not to upload faces, names, addresses, medication bottles, mail, bills, or medical documents.

## Demo Step 3 — AI Hazard Results

The app uses AI to analyze the room photo for visible home fall hazards.

In this example, it may find possible hazards such as a cord near a walking path, a loose rug, or floor clutter.

Each hazard card explains:
- What the hazard is
- Why it matters
- A simple suggested fix

## Demo Step 4 — Checklist

Because AI can miss things, the app also asks checklist questions.

This adds human review to the process.

## Demo Step 5 — Score

The app combines the AI findings and checklist answers into a simple score from 0 to 100.

The score is labeled:
- Low Risk
- Moderate Risk
- High Risk

This is not a medical diagnosis. It is only an educational home-safety score.

## Demo Step 6 — Report

Finally, the app creates a printable safety report.

The report includes:
- Room type
- Risk score
- Possible hazards
- Checklist concerns
- Recommended fixes
- Safety disclaimer
- Human review reminder

## AI Disclosure

I used AI in two ways.

First, the app uses AI to analyze room photos for possible visible fall hazards.

Second, I used AI coding tools to help plan, debug, and improve parts of the project.

I reviewed, modified, tested, and can explain the code myself.

## Safety and Privacy

AI SafeHome does not collect names, addresses, ages, medical history, medications, or real patient photos.

It does not use a login or database.

It does not diagnose medical risk or guarantee fall prevention.

It was tested with staged, non-patient photos only.

## Closing

My goal with AI SafeHome is to make home safety easier to understand for older adults and families.