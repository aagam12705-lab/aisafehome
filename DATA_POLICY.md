# AI SafeHome Data Policy

AI SafeHome is an educational home-safety demo app.

The database feature is designed to store anonymous safety-check results for testing, validation, and project demonstration.

It is not designed to store patient records, medical information, or private personal information.

## Database Purpose

The database may be used to save anonymous room-check results, such as:

- Room type
- AI analysis mode
- Fall-hazard score
- Risk label
- Hazard categories
- Hazard titles
- Recommendations
- Checklist answers
- Whether the checklist was skipped
- Whether a demo/staged example was used
- Timestamp
- App version

## Data That Must Not Be Stored

AI SafeHome must not store:

- Uploaded photos
- Base64 image data
- Names
- Addresses
- Ages
- Phone numbers
- Emails
- Medical history
- Medication lists
- Insurance information
- Doctor or therapist names
- Patient IDs
- Real patient photos
- Faces
- Mail
- Bills
- Medication bottles
- Medical documents
- GPS location

## Photo Rule

Uploaded photos may be temporarily analyzed during the app session, but photos must not be saved to the database.

Testing should use staged, non-patient photos only.

## Medical Safety Rule

AI SafeHome does not:

- Diagnose medical risk
- Predict individual fall risk
- Guarantee fall prevention
- Replace a doctor, therapist, or home-safety professional

AI may miss hazards. Human review is recommended.

## Database Feature Flag

Database saving must be controlled by:

```bash
DATABASE_ENABLED=false