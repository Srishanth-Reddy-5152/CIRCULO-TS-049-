"""CIRCULO - Circular Decision Engine
Evaluates 5 sustainable consumption routes:
Borrow -> Repair -> Reuse -> Buy Used -> Buy New.
Applies weighted multi-factor scoring and generates explainable recommendation checklists.
"""
from typing import Dict, Any, List
from config import DECISION_WEIGHTS, CIRCULARITY_HIERARCHY_SCORES, DEMO_MODE
from db.database import execute_one

def get_price_reference(item_name: str) -> Dict[str, float]:
    """Retrieve demo benchmark prices from price_reference table."""
    key = item_name.lower()
    # Search for matching item_key
    row = execute_one(
        "SELECT repair_cost, used_price, new_price FROM price_reference WHERE ? LIKE '%' || item_key || '%' LIMIT 1",
        (key,)
    )
    if row:
        return {
            "repair_cost": row["repair_cost"],
            "used_price": row["used_price"],
            "new_price": row["new_price"]
        }
    # Generic realistic fallback prices if unlisted
    return {
        "repair_cost": 80.0,
        "used_price": 250.0,
        "new_price": 550.0
    }

def generate_reasons(route: str, item: Dict[str, Any], user: Dict[str, Any], prices: Dict[str, float]) -> List[str]:
    """
    Generate an explainable 'Why CIRCULO recommends this' checklist
    based strictly on underlying data.
    """
    reasons = []
    cap_pct = int(item.get("capability_match_score", 0.0) * 100)
    
    if route == "borrow":
        if cap_pct == 100:
            reasons.append("100% capability match — satisfies all project requirements.")
        elif cap_pct >= 65:
            reasons.append(f"{cap_pct}% capability match — functional alternative ready for use.")
            
        if item.get("availability") == "AVAILABLE" and item.get("quantity_available", 0) > 0:
            reasons.append(f"Available now on campus ({item.get('quantity_available')} units ready for pickup).")
            
        reasons.append(f"Zero cost (₹0 borrow vs ₹{int(prices['new_price'])} retail purchase).")
        
        user_dept = user.get("department", "").lower()
        owner_dept = item.get("owner_department", "").lower()
        if user_dept and owner_dept and (user_dept == owner_dept or "cse" in user_dept and "cse" in owner_dept):
            reasons.append("Located in your department — instant physical handover.")
        else:
            reasons.append(f"Located at {item.get('location', 'Campus Desk')}.")
            
        reasons.append("High circularity — avoids single-semester purchase and future e-waste.")
        reasons.append("Can be returned safely to inventory once your project finishes.")

    elif route == "repair":
        reasons.append(f"Low-cost repair (estimated ₹{int(prices['repair_cost'])}) restores existing equipment.")
        reasons.append("Extends hardware lifespan and diverts functional components from disposal.")
        reasons.append("Assistance available at Campus Makerspace.")

    elif route == "reuse":
        reasons.append("Repurposes a secondary compatible campus asset.")
        reasons.append("Keeps idle campus hardware in active circulation.")
        reasons.append("Zero financial expenditure.")

    elif route == "buy_used":
        reasons.append(f"Affordable second-hand acquisition (est. ₹{int(prices['used_price'])} vs ₹{int(prices['new_price'])} new).")
        reasons.append("Purchasing pre-owned hardware extends product lifecycle.")
        reasons.append("Keeps existing assets in circulation within the student community.")

    elif route == "buy_new":
        reasons.append(f"Brand new commercial product with manufacturer warranty (est. ₹{int(prices['new_price'])}).")
        reasons.append("Guarantees pristine condition if custom specifications require it.")
        reasons.append("Lowest circularity score due to manufacturing and packaging footprint.")

    return reasons

def evaluate_routes(candidate_item: Dict[str, Any], user: Dict[str, Any], requirement: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build and score the 5 circular consumption routes for the top matching candidate.
    """
    prices = get_price_reference(candidate_item["name"])
    w = DECISION_WEIGHTS
    
    cap_score = candidate_item.get("capability_match_score", 0.7)
    is_avail = 1.0 if (candidate_item.get("availability") == "AVAILABLE" and candidate_item.get("quantity_available", 0) > 0) else 0.2
    
    # Proximity score
    user_dept = (user.get("department") or "").lower()
    owner_dept = (candidate_item.get("owner_department") or "").lower()
    proximity_score = 1.0 if (user_dept and owner_dept and user_dept in owner_dept) else 0.75

    routes = []

    # 1. BORROW ROUTE
    borrow_circ = CIRCULARITY_HIERARCHY_SCORES["borrow"] / 100.0  # 0.95
    borrow_cost_score = 1.0  # ₹0 is optimal
    borrow_overall = (
        cap_score * w["compatibility"] +
        is_avail * w["availability"] +
        borrow_cost_score * w["cost"] +
        proximity_score * w["proximity"] +
        borrow_circ * w["circularity"]
    )
    routes.append({
        "route_key": "borrow",
        "title": "Borrow via Campus Network",
        "badge": "Recommended Choice" if is_avail > 0.5 else "Waitlist",
        "score": round(borrow_overall * 100, 1),
        "circularity_score": CIRCULARITY_HIERARCHY_SCORES["borrow"],
        "cost_label": "₹0 (Free Loan)",
        "estimated_cost": 0.0,
        "availability_label": f"Available ({candidate_item.get('quantity_available')} units)" if is_avail > 0.5 else "Currently Loaned",
        "location": candidate_item.get("location", "Campus"),
        "owner": candidate_item.get("owner_name", "Campus Peer"),
        "reasons": generate_reasons("borrow", candidate_item, user, prices),
        "action_label": "Request to Borrow",
        "action_type": "request_borrow",
        "is_recommended": is_avail > 0.5
    })

    # 2. REPAIR ROUTE
    repair_circ = CIRCULARITY_HIERARCHY_SCORES["repair"] / 100.0  # 0.88
    repair_cost_score = max(0.0, 1.0 - (prices["repair_cost"] / prices["new_price"]))
    repair_overall = (
        cap_score * 0.9 * w["compatibility"] +
        0.8 * w["availability"] +
        repair_cost_score * w["cost"] +
        0.8 * w["proximity"] +
        repair_circ * w["circularity"]
    )
    routes.append({
        "route_key": "repair",
        "title": "Repair & Restore Existing Board",
        "badge": "Eco-Repair",
        "score": round(repair_overall * 100, 1),
        "circularity_score": CIRCULARITY_HIERARCHY_SCORES["repair"],
        "cost_label": f"~₹{int(prices['repair_cost'])} (Spare/Labor)",
        "estimated_cost": prices["repair_cost"],
        "availability_label": "Makerspace Workbench",
        "location": "Campus Makerspace & Repair Clinic",
        "owner": "Makerspace Support",
        "reasons": generate_reasons("repair", candidate_item, user, prices),
        "action_label": "Submit Repair Ticket",
        "action_type": "request_repair",
        "is_recommended": False
    })

    # 3. REUSE ROUTE (Compatible alternative on campus)
    reuse_circ = CIRCULARITY_HIERARCHY_SCORES["reuse"] / 100.0  # 0.82
    reuse_overall = (
        cap_score * 0.85 * w["compatibility"] +
        is_avail * w["availability"] +
        1.0 * w["cost"] +
        proximity_score * w["proximity"] +
        reuse_circ * w["circularity"]
    )
    routes.append({
        "route_key": "reuse",
        "title": "Repurpose Campus Alternative",
        "badge": "Circularity Option",
        "score": round(reuse_overall * 100, 1),
        "circularity_score": CIRCULARITY_HIERARCHY_SCORES["reuse"],
        "cost_label": "₹0 (Repurposed)",
        "estimated_cost": 0.0,
        "availability_label": "Available in Lab Storage",
        "location": candidate_item.get("location", "Campus Storage"),
        "owner": "Institutional Inventory",
        "reasons": generate_reasons("reuse", candidate_item, user, prices),
        "action_label": "Claim for Repurposing",
        "action_type": "repurpose",
        "is_recommended": False
    })

    # 4. BUY USED ROUTE
    used_circ = CIRCULARITY_HIERARCHY_SCORES["buy_used"] / 100.0  # 0.70
    used_cost_score = max(0.0, 1.0 - (prices["used_price"] / prices["new_price"]))
    used_overall = (
        cap_score * w["compatibility"] +
        0.8 * w["availability"] +
        used_cost_score * w["cost"] +
        0.6 * w["proximity"] +
        used_circ * w["circularity"]
    )
    routes.append({
        "route_key": "buy_used",
        "title": "Buy Pre-Owned / Refurbished",
        "badge": "Second-Hand",
        "score": round(used_overall * 100, 1),
        "circularity_score": CIRCULARITY_HIERARCHY_SCORES["buy_used"],
        "cost_label": f"~₹{int(prices['used_price'])} (Used)",
        "estimated_cost": prices["used_price"],
        "availability_label": "Senior Student Listing",
        "location": "Campus Classifieds / Notice Board",
        "owner": "Graduating Student",
        "reasons": generate_reasons("buy_used", candidate_item, user, prices),
        "action_label": "Contact Used Seller",
        "action_type": "buy_used",
        "is_recommended": False
    })

    # 5. BUY NEW ROUTE
    new_circ = CIRCULARITY_HIERARCHY_SCORES["buy_new"] / 100.0  # 0.35
    new_cost_score = 0.15  # Retail full price
    new_overall = (
        1.0 * w["compatibility"] +
        0.9 * w["availability"] +
        new_cost_score * w["cost"] +
        0.4 * w["proximity"] +
        new_circ * w["circularity"]
    )
    routes.append({
        "route_key": "buy_new",
        "title": "Buy Brand New Retail",
        "badge": "Last Resort (High Impact)",
        "score": round(new_overall * 100, 1),
        "circularity_score": CIRCULARITY_HIERARCHY_SCORES["buy_new"],
        "cost_label": f"~₹{int(prices['new_price'])} (New)",
        "estimated_cost": prices["new_price"],
        "availability_label": "Online Retail Store (1-3 days delivery)",
        "location": "Amazon / Robocraze / Local Shop",
        "owner": "Commercial Retailer",
        "reasons": generate_reasons("buy_new", candidate_item, user, prices),
        "action_label": "View Retail Listing",
        "action_type": "buy_new",
        "is_recommended": False
    })

    # Sort routes by overall score descending
    routes.sort(key=lambda x: x["score"], reverse=True)
    
    # Ensure the top route is marked recommended
    if routes:
        for r in routes:
            r["is_recommended"] = False
        routes[0]["is_recommended"] = True
        routes[0]["badge"] = "CIRCULO Best Choice"

    return routes
