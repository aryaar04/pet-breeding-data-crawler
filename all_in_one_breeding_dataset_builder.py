import requests
import json
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ================= CONFIG =================

OUTPUT_FILE = "dog_cat_breeding_dataset.json"

SEED_URLS = [
    # Dogs
    "https://vcahospitals.com/know-your-pet/reproduction-in-dogs",
    "https://www.petmd.com/dog/care/dog-breeding",
    "https://www.merckvetmanual.com/reproductive-system",
    "https://www.akc.org/expert-advice/dog-breeding/",

    # Cats
    "https://vcahospitals.com/know-your-pet/reproduction-in-cats",
    "https://www.petmd.com/cat/care/cat-breeding"
]

BREEDING_SIGNAL_TERMS = [
    "estrus", "heat cycle", "ovulation",
    "pregnancy", "gestation",
    "mating", "fertility",
    "whelping", "queening",
    "reproductive", "litter",
    "neonatal", "prenatal",
    "genetic", "hereditary"
]

JUNK_TERMS = [
    "register", "login", "shop", "cart",
    "newsletter", "subscribe", "advertise",
    "event", "award", "breed profile",
    "why does my dog", "symptoms",
    "disease", "treatment", "insurance",
    "form", "transaction"
]

VALID_SPECIES = ["dog", "cat"]

HEADERS = {"User-Agent": "PAWS-AgenticRAG/1.0"}
MAX_PAGES = 150
MIN_TEXT_LEN = 180
MAX_TEXT_LEN = 600

visited = set()
dataset = []
record_id = 1

# ================= HELPERS =================

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text.strip()

def has_breeding_signal(text):
    t = text.lower()
    return any(term in t for term in BREEDING_SIGNAL_TERMS)

def is_junk(text):
    t = text.lower()
    return any(term in t for term in JUNK_TERMS)

def detect_species(text):
    t = text.lower()
    dog = "dog" in t or "canine" in t
    cat = "cat" in t or "feline" in t
    if dog and cat:
        return "both"
    if dog:
        return "dog"
    if cat:
        return "cat"
    return None

def infer_subtopic(text):
    t = text.lower()
    if "estrus" in t or "heat" in t:
        return "estrus_cycle"
    if "pregnancy" in t or "gestation" in t:
        return "pregnancy"
    if "whelp" in t:
        return "whelping"
    if "queen" in t:
        return "queening"
    if "genetic" in t or "hereditary" in t:
        return "genetics"
    if "mating" in t or "fertility" in t:
        return "mating"
    return "general_breeding"

# ================= CRAWLER =================

def crawl(url):
    global record_id

    if url in visited or len(visited) >= MAX_PAGES:
        return []

    visited.add(url)
    print(f"🔍 Crawling: {url}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.decompose()

        for p in soup.find_all("p"):
            text = clean_text(p.get_text())

            if len(text) < MIN_TEXT_LEN or len(text) > MAX_TEXT_LEN:
                continue
            if not has_breeding_signal(text):
                continue
            if is_junk(text):
                continue

            species = detect_species(text)
            if species not in VALID_SPECIES and species != "both":
                continue

            dataset.append({
                "id": record_id,
                "topic": "breeding",
                "species": species,
                "subtopic": infer_subtopic(text),
                "content": text,
                "source_url": url
            })
            record_id += 1

        links = []
        for a in soup.find_all("a", href=True):
            next_url = urljoin(url, a["href"])
            parsed = urlparse(next_url)
            if parsed.scheme.startswith("http") and parsed.netloc:
                if any(k in next_url.lower() for k in ["breed", "reproduction", "pregnancy", "breeding"]):
                    links.append(next_url)

        return links

    except Exception as e:
        return []

# ================= MAIN =================

queue = SEED_URLS.copy()

while queue and len(visited) < MAX_PAGES:
    current = queue.pop(0)
    new_links = crawl(current)
    queue.extend(new_links)
    time.sleep(1)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"\n✅ Breeding dataset created")
print(f"   Records: {len(dataset)}")
print(f"   Output: {OUTPUT_FILE}")
