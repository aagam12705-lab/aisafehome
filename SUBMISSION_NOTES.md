# Congressional App Challenge Submission Notes

## One-sentence purpose

AI SafeHome helps older adults and caregivers turn a room photo into understandable fall-prevention steps.

## Technical challenge

The central challenge was making AI photo analysis useful without treating it like a medical diagnosis. The app separates visible hazards from uncertain details, asks short follow-up questions only when needed, scores each hazard separately, uses category scores only as a fallback, adds an AI-provided uncertainty buffer when questions are skipped, and caps the final score at 100.

## Design choices

The interface was designed for older adults: fewer actions per screen, large mobile-friendly controls, clear color modes, plain English, optional read-aloud support, and a three-step safety plan that keeps the risk score visible without making it the only outcome.

## Responsible AI

The app labels sample results, shows approximate visual hazard locations, explains that AI can miss or misunderstand hazards, does not make medical claims, and keeps photo storage out of the application database.
