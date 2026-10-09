"""CIRCULO - Matching Engine
Combines Capability Overlap Scoring with TF-IDF / Cosine Similarity (scikit-learn).
Ranks campus inventory and identifies compatible alternatives.
"""
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from db.database import execute_query

def compute_name_match_score(query: str, item_name: str) -> float:
    """
    Score how strongly a user query targets an item by name.
    Handles exact names, substrings, word intersections, and typo tolerance.
    """
    q = query.lower().strip()
    name = item_name.lower().strip()

    if not q or not name:
        return 0.0

    # 1. Exact match
    if q == name:
        return 1.0

    # 2. Substring match (either query in item name, or item name in query)
    if q in name or name in q:
        return 0.90

    # 3. Word-level token match (ignoring generic intent words)
    noise_words = {
        'need', 'want', 'looking', 'project', 'campus', 'help', 'resource',
        'require', 'something', 'work', 'test', 'lab', 'hall', 'room'
    }
    q_words = [w for w in re.findall(r'\b[a-z0-9]{3,}\b', q) if w not in noise_words]
    name_words = re.findall(r'\b[a-z0-9]{3,}\b', name)

    if q_words and name_words:
        common_words = set(q_words).intersection(set(name_words))
        if common_words:
            return 0.80 * (len(common_words) / max(len(q_words), 1))

        # Check fuzzy token similarity (e.g. 'ardo' vs 'arduino')
        for qw in q_words:
            for nw in name_words:
                ratio = SequenceMatcher(None, qw, nw).ratio()
                if ratio >= 0.70:
                    return 0.75 * ratio

    # 4. Full string fuzzy ratio
    full_ratio = SequenceMatcher(None, q, name).ratio()
    if full_ratio >= 0.65:
        return 0.70 * full_ratio

    return 0.0

def get_available_inventory() -> List[Dict[str, Any]]:
    """
    Fetch all active items along with their capabilities and owner details.
    """
    query = """
    SELECT 
        i.id, i.owner_id, i.name, i.category_id, i.description, i.condition,
        i.location, i.quantity, i.quantity_available, i.availability,
        i.available_for, i.available_until, i.last_used, i.image_path,
        u.name as owner_name, u.department as owner_department, u.role as owner_role,
        c.name as category_name
    FROM items i
    JOIN users u ON i.owner_id = u.id
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE i.availability != 'UNAVAILABLE'
    """
    items = execute_query(query)
    
    # Attach capabilities for each item
    for item in items:
        caps_rows = execute_query(
            "SELECT capability FROM item_capabilities WHERE item_id = ?",
            (item["id"],)
        )
        item["capabilities"] = [r["capability"] for r in caps_rows]
    return items

def find_matches(requirement: Dict[str, Any], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Match candidate items against the parsed requirement.
    Calculates:
    - capability_match_score = matched_caps / required_caps
    - name_match_score = direct title / keyword match (exact, substring, fuzzy)
    - tfidf_score = cosine similarity between search query & item text
    - blended_score = balanced hybrid rank
    """
    items = get_available_inventory()
    if not items:
        return []

    required_caps = set(requirement.get("required_capabilities", []))
    raw_query = requirement.get("raw_text", requirement.get("need", "")).lower()

    # Build corpus for TF-IDF
    corpus = []
    for item in items:
        caps_str = " ".join(item.get("capabilities", []))
        doc = f"{item['name']} {item.get('description', '')} {item.get('category_name', '')} {caps_str}".lower()
        corpus.append(doc)

    # Compute TF-IDF similarities
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus + [raw_query])
        query_vec = tfidf_matrix[-1]
        item_vecs = tfidf_matrix[:-1]
        cosine_sims = cosine_similarity(query_vec, item_vecs).flatten()
    except Exception:
        # Fallback if scikit-learn vectorizer has empty vocabulary
        cosine_sims = [0.0] * len(items)

    candidates = []
    for idx, item in enumerate(items):
        item_caps = set(item.get("capabilities", []))
        matched = required_caps.intersection(item_caps)

        if required_caps:
            cap_score = len(matched) / len(required_caps)
        else:
            cap_score = 0.5

        name_score = compute_name_match_score(raw_query, item["name"])
        tfidf_val = float(cosine_sims[idx]) if idx < len(cosine_sims) else 0.0

        # Blended ranking score (Balances capability requirements AND object name search)
        if cap_score > 0 and name_score > 0:
            blended = 0.45 * cap_score + 0.35 * name_score + 0.20 * min(tfidf_val * 1.5, 1.0)
        elif name_score > 0:
            blended = 0.65 * name_score + 0.35 * min(tfidf_val * 1.5, 1.0)
        elif cap_score > 0:
            blended = 0.70 * cap_score + 0.30 * min(tfidf_val * 1.5, 1.0)
        else:
            blended = tfidf_val * 0.60

        # Keep item if capability matched OR name matched OR blended score is relevant
        if cap_score > 0 or name_score >= 0.30 or blended > 0.15:
            candidates.append({
                **item,
                "matched_capabilities": sorted(list(matched)),
                "unmatched_capabilities": sorted(list(required_caps - matched)),
                "capability_match_score": round(cap_score, 2),
                "name_match_score": round(name_score, 2),
                "tfidf_score": round(tfidf_val, 2),
                "blended_score": round(blended, 2),
            })

    # Sort descending by blended_score, then capability_match_score
    candidates.sort(key=lambda x: (x["blended_score"], x["capability_match_score"]), reverse=True)
    return candidates[:top_n]
