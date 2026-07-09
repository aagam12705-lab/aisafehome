# AI SafeHome Submission Notes

## One-Sentence Description

AI SafeHome is a Python Streamlit web app that helps older adults and families identify possible home fall hazards from room photos and a checklist, then creates a plain-English safety report.

## Problem

Older adults and families may not notice common fall hazards such as loose rugs, cords, clutter, poor lighting, stairs, slippery floors, and bathroom risks.

## Solution

AI SafeHome gives users a simple step-by-step safety check:

1. Select a room
2. Upload or take a staged room photo
3. Review AI hazard suggestions
4. Answer checklist questions
5. Get a 0–100 hazard score
6. Create a printable safety report

## Technology Used

- Python
- Streamlit
- Pillow
- python-dotenv
- OpenAI API
- GitHub
- Streamlit Community Cloud

## AI Use

AI SafeHome uses AI vision analysis to identify possible visible environmental fall hazards in room photos.

AI was also used as a coding assistant for brainstorming, debugging, and improving the project.

The student reviewed, modified, tested, and understands the app.

## Privacy and Safety Limits

The app does not collect:

- Names
- Addresses
- Ages
- Medical history
- Medications
- Insurance information
- Real patient photos

The app does not:

- Use a login
- Use a database
- Store photos
- Diagnose medical risk
- Guarantee fall prevention
- Replace a doctor, therapist, or home-safety professional

## Scoring Algorithm

The app uses a simple point system:

- Loose rug or mat: 10
- Cord across walking path: 12
- Floor clutter: 10
- Poor lighting: 8
- Slippery or wet floor: 12
- Narrow or blocked pathway: 8
- Stairs or step hazard: 15
- Missing or unsafe handrail: 15
- Bathroom without grab bars: 15
- Items hard to reach: 6

Checklist scoring:

- Yes = full points
- Not sure = half points
- No = 0 points
- Not applicable = 0 points

Risk levels:

- 0–29 = Low Risk
- 30–59 = Moderate Risk
- 60–100 = High Risk

## Judging Rubric Alignment

### Creativity

AI SafeHome combines AI photo analysis with a human checklist and creates a practical report.

### Technical Skill

The project includes image upload, AI vision analysis, JSON processing, scoring logic, session state, and report generation.

### Usefulness

The app helps families notice common home hazards in plain English.

### Design

The app is designed for iPhone Safari with large buttons, simple labels, and readable text.

### Student Ownership

The student can explain:

- The app flow
- The Python files
- The AI analysis function
- The scoring algorithm
- The safety disclaimers
- The privacy limits