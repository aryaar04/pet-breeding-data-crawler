import json
import re

INPUT_FILE = "dog_cat_breeding_dataset.json"
OUTPUT_FILE = "dog_cat_breeding_dataset_clean.json"

# --------------------------------------------------
# STEP 1: HARD DELETE TERMS (ADMIN / UI / NOISE)
# --------------------------------------------------

ADMIN_TERMS = [
    "application", "apply", "form", "transaction",
    "register", "registration", "portal",
    "manage", "dashboard", "login", "sign in",
    "program", "award", "breeder of merit",
    "interview", "story", "experience",
    "fee", "payment", "contract",
    "search using", "certificate",
    "customer reply", "akc number"
]

# --------------------------------------------------
# STEP 2: REQUIRED BIOLOGICAL BREEDING SIGNALS
# (at least ONE must appear)
# --------------------------------------------------

BREEDING_SIGNALS = [
    "estrus", "heat cycle", "ovulation",
    "mating", "fertility",
    "pregnancy", "gestation",
    "whelping", "queening",
    "litter", "neonatal",
    "reproductive", "breeding age",
    "genetic", "hereditary"
]

# --------------------------------------------------
# STEP 3: SPECIES NORMALIZATION RULES
# --------------------------------------------------

DOG_TERMS = [
    "dog", "canine", "bitch", "puppy",
    "stud", "sire", "dam", "whelp"
]

CAT_TERMS = [
    "cat", "feline", "queen", "kitten", "queening"
]

# --------------------------------------------------

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()

def contains_any(text, terms):
    return any(t in text for t in terms)

def normalize_species(text):
    has_dog = contains_any(text, DOG_TERMS)
    has_cat = contains_any(text, CAT_TERMS)

    if has_dog and has_cat:
        return "both"
    if has_dog:
        return "dog"
    if has_cat:
        return "cat"
    return None

# --------------------------------------------------
# MAIN CLEANING PIPELINE
# --------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned = []
new_id = 1

for record in data:
    content = record.get("content", "")
    text = clean_text(content)

    # STEP 1: REMOVE ADMIN / UI / STORIES
    if contains_any(text, ADMIN_TERMS):
        continue

    # STEP 2: REQUIRE BIOLOGICAL BREEDING SIGNAL
    if not contains_any(text, BREEDING_SIGNALS):
        continue

    # STEP 3: FIX SPECIES
    species = normalize_species(text)
    if species is None:
        continue

    cleaned.append({
        "id": new_id,
        "topic": "breeding",
        "species": species,
        "subtopic": record.get("subtopic", "general_breeding"),
        "content": record.get("content", "").strip(),
        "source_url": record.get("source_url", "")
    })

    new_id += 1

# --------------------------------------------------
# SAVE CLEAN DATASET
# --------------------------------------------------

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2, ensure_ascii=False)

print("✅ FINAL CLEANUP COMPLETE")
print(f"Original records: {len(data)}")
print(f"Clean records: {len(cleaned)}")
print(f"Saved to: {OUTPUT_FILE}")
