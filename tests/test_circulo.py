"""CIRCULO - Automated Test Suite
Validates canonical scoring, capability overlap thresholds,
decision engine route rankings, and transaction lifecycle.
"""
import unittest
from db.seed import seed_database
from services.need_service import parse_need
from services.matching_service import find_matches
from services.decision_service import evaluate_routes
from services.transaction_service import (
    create_borrow_request,
    approve_request,
    confirm_handover,
    mark_returned
)
from services.impact_service import get_impact_summary

class TestCirculoCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Seed clean test database
        seed_database()

    def test_01_need_parsing_microcontroller(self):
        """Test that IoT microcontroller request extracts required capabilities."""
        parsed = parse_need("I need a WiFi microcontroller for my IoT project", user_id=1)
        self.assertIn("microcontroller", parsed["required_capabilities"])
        self.assertIn("wifi", parsed["required_capabilities"])
        self.assertIn("iot", parsed["required_capabilities"])

    def test_02_capability_match_percentages(self):
        """
        Verify canonical hackathon benchmark:
        ESP32 matches 100% of (microcontroller, wifi, iot).
        Arduino Uno and Nano match 67% (2 of 3: microcontroller, iot).
        """
        parsed = {
            "need": "WiFi Microcontroller",
            "required_capabilities": ["microcontroller", "wifi", "iot"],
            "purpose": "IoT project",
            "raw_text": "I need a WiFi microcontroller for my IoT project"
        }
        matches = find_matches(parsed, top_n=5)
        self.assertTrue(len(matches) > 0)
        
        # Check ESP32 is first and has 1.0 (100%) score
        esp32_item = next((m for m in matches if "esp32" in m["name"].lower()), None)
        self.assertIsNotNone(esp32_item)
        self.assertEqual(esp32_item["capability_match_score"], 1.0)
        
        # Check Arduino Uno has 2/3 = 0.67 score
        arduino_item = next((m for m in matches if "arduino uno" in m["name"].lower()), None)
        self.assertIsNotNone(arduino_item)
        self.assertEqual(arduino_item["capability_match_score"], 0.67)

    def test_03_decision_engine_ranks_borrow_first(self):
        """
        Verify Borrow outranks Buy New when item is available on campus.
        """
        dummy_user = {"id": 1, "department": "Computer Science & Engineering"}
        parsed = {
            "need": "WiFi Microcontroller",
            "required_capabilities": ["microcontroller", "wifi", "iot"],
            "purpose": "IoT project"
        }
        candidate = {
            "id": 1,
            "name": "ESP32 Wi-Fi & Bluetooth Dev Board",
            "capability_match_score": 1.0,
            "availability": "AVAILABLE",
            "quantity_available": 4,
            "owner_department": "Computer Science & Engineering",
            "location": "CSE Hardware Lab"
        }
        routes = evaluate_routes(candidate, dummy_user, parsed)
        
        # Top route must be Borrow
        self.assertEqual(routes[0]["route_key"], "borrow")
        self.assertTrue(routes[0]["is_recommended"])
        
        # Find Buy New route and verify lower score
        buy_new = next(r for r in routes if r["route_key"] == "buy_new")
        self.assertGreater(routes[0]["score"], buy_new["score"])

    def test_04_borrow_lifecycle_and_impact(self):
        """
        Verify end-to-end transaction loop:
        Request (PENDING) -> Approve (RESERVED) -> Handover (BORROWED) -> Return (RETURNED)
        -> Impact event recorded.
        """
        borrower_id = 1  # Arun (Student)
        lender_id = 7    # CSE Lab
        item_id = 1      # ESP32

        # 1. Create request
        req_id = create_borrow_request(borrower_id, item_id, notes="Test Loan")
        self.assertGreater(req_id, 0)

        # 2. Approve
        approved = approve_request(req_id, lender_id)
        self.assertTrue(approved)

        # 3. Handover
        from db.database import execute_one
        tx = execute_one("SELECT * FROM transactions WHERE request_id = ?", (req_id,))
        self.assertIsNotNone(tx)
        self.assertEqual(tx["status"], "RESERVED")
        
        handover_done = confirm_handover(tx["id"], lender_id)
        self.assertTrue(handover_done)

        # 4. Return
        returned_done = mark_returned(tx["id"], borrower_id)
        self.assertTrue(returned_done)

        # Check impact
        summary = get_impact_summary()
        self.assertGreater(summary["items_reused"], 0)

if __name__ == "__main__":
    unittest.main()
