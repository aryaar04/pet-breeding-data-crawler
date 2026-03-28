import json
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

INPUT_FILE = "dog_cat_breeding_dataset_clean.json"
OUTPUT_FILE = "dog_cat_breeding_dataset_optimized.json"

SIMILARITY_THRESHOLD = 0.92   # aggressive but safe
MIN_LENGTH = 180

BREEDING_KEYWORDS = [
    "estrus", "heat cycle", "ovulation", "mating", "pregnancy",
    "gestation", "whelping", "queening", "fertility",
    "semen", "sperm", "genetic", "reproduction", "litter"
]

SUBTOPIC_MAP = {
    "estrus": "estrus_cycle",
    "heat": "estrus_cycle",
    "ovulation": "estrus_cycle",
    "mating": "mating",
    "pregnancy": "pregnancy",
    "gestation": "pregnancy",
    "whelp": "whelping",
    "queening": "queening",
    "genetic": "genetics",
    "semen": "genetics",
    "fertility": "fertility"
}

DOG_HINTS = ["dog", "canine", "bitch", "whelp"]
CAT_HINTS = ["cat", "feline", "queen", "queening"]

model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(t):
    return re.sub(r"\s+", " ", t).strip()

def infer_species(text):
    t = text.lower()
    d = sum(w in t for w in DOG_HINTS)
    c = sum(w in t for w in CAT_HINTS)
    if d and c:
        return "both"
    if d:
        return "dog"
    if c:
        return "cat"
    return "both"

def infer_subtopic(text):
    t = text.lower()
    for k, v in SUBTOPIC_MAP.items():
        if k in t:
            return v
    return "general_breeding"

def breeding_relevant(text):
    t = text.lower()
    return any(k in t for k in BREEDING_KEYWORDS)

# ------------------ LOAD ------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"🔹 Loaded {len(data)} records")

# ------------------ FILTER ------------------

filtered = []
for r in data:
    content = clean_text(r["content"])
    if len(content) < MIN_LENGTH:
        continue
    if not breeding_relevant(content):
        continue

    r["content"] = content
    r["species"] = infer_species(content)
    r["subtopic"] = infer_subtopic(content)
    filtered.append(r)

print(f"✅ After relevance filtering: {len(filtered)} records")

# ------------------ DEDUPLICATION ------------------

texts = [r["content"] for r in filtered]
embeddings = model.encode(texts, show_progress_bar=True)
similarity = cosine_similarity(embeddings)

keep = []
removed = set()

for i in range(len(filtered)):
    if i in removed:
        continue
    keep.append(filtered[i])
    for j in range(i + 1, len(filtered)):
        if similarity[i][j] > SIMILARITY_THRESHOLD:
            removed.add(j)

print(f"🧹 Removed {len(removed)} near-duplicates")
print(f"✅ Final optimized records: {len(keep)}")

# ------------------ RE-ID ------------------

for i, r in enumerate(keep, start=1):
    r["id"] = i

# ------------------ SAVE ------------------

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(keep, f, indent=2, ensure_ascii=False)

print(f"\n📦 Optimized dataset saved to: {OUTPUT_FILE}")
