# AI SafeHome Testing Checklist

AI SafeHome is tested using staged, non-patient photos only.

Do not test with:
- Faces
- Names
- Addresses
- Mail
- Bills
- Medication bottles
- Medical documents
- Real patient photos
- Medical history

## Test Devices

- Laptop browser:
- iPhone Safari:
- Deployed Streamlit app link:

## Full Demo Flow Test

### 1. Landing Page

Expected:
- App name appears
- Tagline appears
- Safety disclaimer appears
- Privacy reminder appears
- Start Safety Check button works

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 2. Room Selection

Expected:
- Room options appear:
  - Living Room
  - Bedroom
  - Bathroom
  - Kitchen
  - Hallway
  - Stairs
  - Other
- User can select each room
- Continue button works
- Back button works

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 3. Photo Upload

Expected:
- User can upload or take a staged room photo
- JPG, JPEG, PNG, or WEBP works
- Photo preview appears
- Privacy warning appears
- App does not ask for personal information

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 4. Fake AI Hazard Results

Expected:
- Analyze Photo button works
- Fake AI-style hazards appear
- Hazard cards include:
  - Hazard title
  - Category
  - Why it matters
  - Suggested fix
- Safety reminder appears

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 5. Checklist

Expected:
- All 10 checklist questions appear
- Each question has:
  - Yes
  - No
  - Not sure
  - Not applicable
- Save Checklist works
- Checklist summary appears

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 6. Risk Score

Expected:
- Score appears from 0 to 100
- Risk label appears:
  - Low Risk
  - Moderate Risk
  - High Risk
- Top concerns appear
- Recommended first fixes appear
- Score breakdown opens

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### 7. Safety Report

Expected:
- Safety report is created
- Report includes:
  - Date
  - Room type
  - Score
  - Risk level
  - AI hazards
  - Checklist concerns
  - Recommended fixes
  - Safety disclaimer
  - Human review reminder
  - Privacy reminder
- Download report button works
- Print/save instructions appear

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

## iPhone Safari Test

Expected:
- No sideways scrolling
- Buttons are easy to tap
- Text is readable without zooming
- Upload works
- Checklist is usable
- Report is readable

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

## Score Test Cases

### Test Case 1: Living Room

Expected fake AI hazards:
- Cord hazard
- Loose rug
- Floor clutter

Expected AI-only score:
- 12 + 10 + 10 = 32
- Moderate Risk

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### Test Case 2: Bathroom

Expected fake AI hazards:
- Bathroom grab bar concern
- Slippery floor

Expected AI-only score:
- 15 + 12 = 27
- Low Risk

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

### Test Case 3: Stairs

Expected fake AI hazards:
- Stairs
- Handrail

Expected AI-only score:
- 15 + 15 = 30
- Moderate Risk

Result:
- [ ] Pass
- [ ] Fail

Notes:

---

## Final Demo Readiness

The app is demo-ready when:

- [ ] Full flow works on laptop
- [ ] Full flow works on iPhone Safari
- [ ] Deployed Streamlit link works
- [ ] At least 3 staged photos are tested
- [ ] No real patient photos are used
- [ ] No personal or medical data is collected
- [ ] Report downloads successfully
- [ ] Student can explain the scoring algorithm
- [ ] Student can explain that fake AI is being used before real AI integration
- [ ] Student can explain privacy and safety limits