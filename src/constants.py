APP_NAME = "AI SafeHome"
TAGLINE = "Find home fall hazards before they become accidents."

LANDING_EXPLANATION = (
    "Upload a staged room photo, answer a few simple questions, and AI SafeHome "
    "will help identify possible fall hazards such as loose rugs, cords, clutter, "
    "poor lighting, stairs, slippery floors, and bathroom risks."
)

SAFETY_DISCLAIMER = (
    "AI SafeHome is an educational home-safety tool. It does not diagnose medical "
    "conditions, predict individual fall risk, or guarantee fall prevention. AI may "
    "miss hazards. For serious safety concerns, ask a qualified professional to review the home."
)

PRIVACY_REMINDER = (
    "Use staged, non-patient photos only. Avoid faces, names, addresses, mail, bills, "
    "medication bottles, and medical documents."
)

PHOTO_UPLOAD_PRIVACY_WARNING = (
    "Before uploading, avoid including faces, names, addresses, medication bottles, "
    "mail, bills, or medical documents in the photo."
)

PHOTO_NOT_STORED_NOTE = (
    "Uploaded photos are used only during this app session. This app does not save photos to the database."
)

ROOM_OPTIONS = [
    "Living Room",
    "Bedroom",
    "Bathroom",
    "Kitchen",
    "Hallway",
    "Stairs",
    "Dining Room",
    "Laundry Room",
    "Garage",
    "Entryway / Foyer",
    "Basement",
    "Outdoor Walkway / Porch",
    "Closet / Storage Area",
    "Home Office",
    "Other",
]

ALLOWED_FILE_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_FILE_SIZE_MB = 5

CATEGORY_LABELS = {
    "loose_rug": "Loose Rug or Mat",
    "cords": "Cord Hazard",
    "clutter": "Floor Clutter",
    "poor_lighting": "Poor Lighting",
    "slippery_floor": "Slippery or Wet Floor",
    "narrow_pathway": "Narrow or Blocked Pathway",
    "stairs": "Stairs or Step Hazard",
    "handrail": "Handrail Concern",
    "bathroom_grab_bars": "Bathroom Grab Bar Concern",
    "hard_to_reach_items": "Hard-to-Reach Items",
    "threshold_trip": "Raised Threshold or Floor Transition",
    "unstable_furniture": "Unstable Furniture",
    "pet_items": "Pet Items in Walking Path",
    "footwear": "Shoes or Footwear in Walking Path",
    "low_seating": "Low or Unsafe Seating",
    "poor_contrast": "Poor Contrast / Hard-to-See Edges",
    "uneven_floor": "Uneven Floor Surface",
    "door_mat": "Loose Door Mat",
    "furniture_in_path": "Furniture Blocking Walking Path",
    "outdoor_surface": "Outdoor Surface Hazard",
    "laundry_on_floor": "Laundry on Floor",
    "open_drawers_cabinets": "Open Drawers or Cabinets",
    "unclear": "Unclear Hazard",
}

HAZARD_POINTS = {
    "loose_rug": 10,
    "cords": 12,
    "clutter": 10,
    "poor_lighting": 8,
    "slippery_floor": 12,
    "narrow_pathway": 8,
    "stairs": 15,
    "handrail": 15,
    "bathroom_grab_bars": 15,
    "hard_to_reach_items": 6,
    "threshold_trip": 10,
    "unstable_furniture": 10,
    "pet_items": 6,
    "footwear": 6,
    "low_seating": 8,
    "poor_contrast": 6,
    "uneven_floor": 12,
    "door_mat": 8,
    "furniture_in_path": 8,
    "outdoor_surface": 12,
    "laundry_on_floor": 8,
    "open_drawers_cabinets": 8,
}

GENERIC_RECOMMENDATIONS = {
    "loose_rug": "Add non-slip backing, tape down rug edges, or remove the rug from the walking path.",
    "cords": "Move cords along the wall or secure them with a cord cover.",
    "clutter": "Clear shoes, bags, boxes, and small objects from the floor.",
    "poor_lighting": "Add brighter lighting or night lights near walking paths.",
    "slippery_floor": "Keep the floor dry and use non-slip mats where needed.",
    "narrow_pathway": "Move furniture or objects to create a wider walking path.",
    "stairs": "Keep stairs clear, improve lighting, and make step edges easy to see.",
    "handrail": "Check that handrails are secure, easy to grip, and available where needed.",
    "bathroom_grab_bars": "Consider properly installed grab bars near the toilet, shower, or bathtub.",
    "hard_to_reach_items": "Move commonly used items to easy-to-reach shelves or counters.",
    "threshold_trip": "Make floor transitions easier to see and keep thresholds clear.",
    "unstable_furniture": "Secure or replace furniture that may slide, wobble, or be hard to use for support.",
    "pet_items": "Move pet bowls, toys, beds, and leashes away from walking paths.",
    "footwear": "Store shoes and slippers away from walkways.",
    "low_seating": "Use stable chairs that are easier to sit in and stand up from.",
    "poor_contrast": "Improve contrast on step edges, thresholds, or floor changes so they are easier to see.",
    "uneven_floor": "Repair or clearly mark uneven flooring, bumps, or lifted edges.",
    "door_mat": "Use a non-slip mat or remove loose mats from entry areas.",
    "furniture_in_path": "Move furniture so walking paths are open and easy to navigate.",
    "outdoor_surface": "Clear leaves, ice, water, loose mats, or uneven areas from outdoor walking surfaces.",
    "laundry_on_floor": "Keep laundry baskets and loose clothing away from the floor and walking paths.",
    "open_drawers_cabinets": "Keep drawers and cabinet doors closed when not in use.",
}

PRIORITY_FIX_NOW = "Fix Now"
PRIORITY_FIX_SOON = "Fix Soon"
PRIORITY_WATCH_REVIEW = "Watch/Review"

CATEGORY_PRIORITY = {
    "cords": PRIORITY_FIX_NOW,
    "slippery_floor": PRIORITY_FIX_NOW,
    "stairs": PRIORITY_FIX_NOW,
    "handrail": PRIORITY_FIX_NOW,
    "bathroom_grab_bars": PRIORITY_FIX_NOW,
    "threshold_trip": PRIORITY_FIX_NOW,
    "uneven_floor": PRIORITY_FIX_NOW,
    "outdoor_surface": PRIORITY_FIX_NOW,
    "open_drawers_cabinets": PRIORITY_FIX_NOW,

    "loose_rug": PRIORITY_FIX_SOON,
    "clutter": PRIORITY_FIX_SOON,
    "narrow_pathway": PRIORITY_FIX_SOON,
    "poor_lighting": PRIORITY_FIX_SOON,
    "hard_to_reach_items": PRIORITY_FIX_SOON,
    "unstable_furniture": PRIORITY_FIX_SOON,
    "door_mat": PRIORITY_FIX_SOON,
    "furniture_in_path": PRIORITY_FIX_SOON,
    "laundry_on_floor": PRIORITY_FIX_SOON,
    "low_seating": PRIORITY_FIX_SOON,
    "poor_contrast": PRIORITY_FIX_SOON,

    "pet_items": PRIORITY_WATCH_REVIEW,
    "footwear": PRIORITY_WATCH_REVIEW,
    "unclear": PRIORITY_WATCH_REVIEW,
}

PRIORITY_ORDER = {
    PRIORITY_FIX_NOW: 1,
    PRIORITY_FIX_SOON: 2,
    PRIORITY_WATCH_REVIEW: 3,
}