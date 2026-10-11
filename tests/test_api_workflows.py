"""Integration and API workflow tests for FasalSense."""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


class ApiWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "FasalSense")
        self.assertIn("Chharoli Budruk", data["target_area"])

    def test_farmer_and_retailer_workflows(self):
        # 1. Register a new farmer
        farmer_email = f"farmer_{abs(hash(str(self)))}@example.com"
        res = self.client.post("/api/auth/register", json={
            "name": "Test Farmer Tukaram",
            "email": farmer_email,
            "password": "FarmerPassword123!",
            "role": "farmer",
            "locality": "Chharoli Budruk"
        })
        self.assertEqual(res.status_code, 200, res.text)
        farmer_data = res.json()
        farmer_token = farmer_data["token"]
        self.assertEqual(farmer_data["user"]["role"], "farmer")

        # 2. Register a new retailer
        retailer_email = f"retailer_{abs(hash(str(self)))}@example.com"
        res = self.client.post("/api/auth/register", json={
            "name": "Chharoli Mandi Buyer",
            "email": retailer_email,
            "password": "RetailerPassword123!",
            "role": "retailer",
            "locality": "Chharoli Budruk"
        })
        self.assertEqual(res.status_code, 200, res.text)
        retailer_data = res.json()
        retailer_token = retailer_data["token"]
        self.assertEqual(retailer_data["user"]["role"], "retailer")

        # 3. Farmer updates farm profile
        farmer_auth = {"Authorization": f"Bearer {farmer_token}"}
        retailer_auth = {"Authorization": f"Bearer {retailer_token}"}

        res = self.client.put("/api/farm", headers=farmer_auth, json={
            "area_acres": 2.5,
            "soil_type": "Black soil",
            "soil_ph": 7.4,
            "nitrogen": 210.0,
            "phosphorus": 22.0,
            "potassium": 180.0,
            "irrigation": "Drip",
            "water_availability": "Reliable",
            "budget_inr": 45000,
            "current_crop": "Sorghum (Jowar)",
            "season": "Rabi"
        })
        self.assertEqual(res.status_code, 200)
        farm_profile = res.json()
        self.assertEqual(farm_profile["area_acres"], 2.5)
        self.assertEqual(farm_profile["soil_ph"], 7.4)

        # 4. Role boundary check: Retailer CANNOT access /api/farm
        res = self.client.get("/api/farm", headers=retailer_auth)
        self.assertEqual(res.status_code, 403)

        # 5. Farmer creates a produce listing
        res = self.client.post("/api/listings", headers=farmer_auth, json={
            "crop_name": "Sorghum (Jowar)",
            "variety": "Maldandi 35-1",
            "quantity_kg": 600,
            "price_per_kg": 34.0,
            "available_date": "Ready for harvest",
            "quality": "Premium grain",
            "description": "Locally harvested Maldandi Jowar in Chharoli."
        })
        self.assertEqual(res.status_code, 200)
        listing_id = res.json()["id"]

        # 6. Role boundary check: Retailer CANNOT create produce listing
        res = self.client.post("/api/listings", headers=retailer_auth, json={
            "crop_name": "Wheat",
            "variety": "Lokwan",
            "quantity_kg": 500,
            "price_per_kg": 28.0,
            "available_date": "Now",
            "quality": "Standard",
            "description": "Unauthorized"
        })
        self.assertEqual(res.status_code, 403)

        # 7. Retailer searches marketplace and finds listing
        res = self.client.get("/api/listings?q=Jowar")
        self.assertEqual(res.status_code, 200)
        listings = res.json()
        self.assertTrue(any(l["id"] == listing_id for l in listings))

        # 8. Retailer submits purchase inquiry
        res = self.client.post("/api/inquiries", headers=retailer_auth, json={
            "listing_id": listing_id,
            "quantity_kg": 150.0,
            "message": "We need 150 kg for our weekly retail dispatch."
        })
        self.assertEqual(res.status_code, 200)
        inquiry_id = res.json()["id"]
        self.assertEqual(res.json()["status"], "Pending")

        # 9. Farmer views inquiries and accepts it
        res = self.client.get("/api/inquiries", headers=farmer_auth)
        self.assertEqual(res.status_code, 200)
        inquiries = res.json()
        self.assertTrue(any(i["id"] == inquiry_id for i in inquiries))

        res = self.client.patch(f"/api/inquiries/{inquiry_id}?status=Accepted", headers=farmer_auth)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "Accepted")

        # 10. Retailer verifies inquiry status changed to Accepted
        res = self.client.get("/api/inquiries", headers=retailer_auth)
        self.assertEqual(res.status_code, 200)
        ret_inquiries = res.json()
        my_inq = next(i for i in ret_inquiries if i["id"] == inquiry_id)
        self.assertEqual(my_inq["status"], "Accepted")

    def test_market_supply_demand_endpoints(self):
        # Hybrid mode (default)
        res = self.client.get("/api/market/supply-demand?mode=hybrid")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("signals", data)
        self.assertGreaterEqual(len(data["signals"]), 16)

        # Platform-only mode
        res = self.client.get("/api/market/supply-demand?mode=platform_only")
        self.assertEqual(res.status_code, 200)
        data_plat = res.json()
        self.assertEqual(data_plat["mode"], "platform_only")

    def test_scenarios_endpoint(self):
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_scenarios"], 7)

    def test_demo_logins_succeed_on_fresh_database(self):
        # Farmer demo login
        res_f = self.client.post("/api/auth/login", json={
            "email": "farmer.demo@example.com",
            "password": "DemoFarm123!"
        })
        self.assertEqual(res_f.status_code, 200, res_f.text)
        data_f = res_f.json()
        self.assertEqual(data_f["user"]["role"], "farmer")
        self.assertTrue(len(data_f["token"]) > 20)

        # Retailer demo login
        res_r = self.client.post("/api/auth/login", json={
            "email": "retailer.demo@example.com",
            "password": "DemoRetail123!"
        })
        self.assertEqual(res_r.status_code, 200, res_r.text)
        data_r = res_r.json()
        self.assertEqual(data_r["user"]["role"], "retailer")
        self.assertTrue(len(data_r["token"]) > 20)

    def test_authenticated_analysis_history_growth(self):
        # 1. Login as demo farmer
        res_login = self.client.post("/api/auth/login", json={
            "email": "farmer.demo@example.com",
            "password": "DemoFarm123!"
        })
        self.assertEqual(res_login.status_code, 200)
        farmer_token = res_login.json()["token"]
        headers = {"Authorization": f"Bearer {farmer_token}"}

        # 2. Check initial history count
        res_hist_initial = self.client.get("/api/analysis-history", headers=headers)
        self.assertEqual(res_hist_initial.status_code, 200)
        initial_count = len(res_hist_initial.json())

        # 3. Perform analysis with authentication
        res_analyze = self.client.post("/api/analyze", headers=headers, json={
            "area_acres": 2.0,
            "soil_type": "Black soil",
            "soil_ph": 7.2,
            "nitrogen": 220.0,
            "phosphorus": 24.0,
            "potassium": 190.0,
            "irrigation": "Drip",
            "water_availability": "Reliable",
            "budget_inr": 40000,
            "season": "Kharif"
        })
        self.assertEqual(res_analyze.status_code, 200)
        self.assertTrue(res_analyze.json().get("history_recorded"))

        # 4. Verify history count grew from initial_count to initial_count + 1
        res_hist_after = self.client.get("/api/analysis-history", headers=headers)
        self.assertEqual(res_hist_after.status_code, 200)
        history = res_hist_after.json()
        self.assertEqual(len(history), initial_count + 1)
        latest = history[0]
        self.assertEqual(latest["area_acres"], 2.0)
        self.assertEqual(latest["budget_inr"], 40000)
        self.assertTrue(len(latest["top_crop"]) > 0)
        self.assertGreater(latest["top_score"], 0)

    def test_zero_budget_marks_every_crop_unaffordable(self):
        res = self.client.post("/api/analyze", json={
            "area_acres": 1.0,
            "soil_type": "Loamy",
            "soil_ph": 6.8,
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip",
            "budget_inr": 0
        })
        self.assertEqual(res.status_code, 200)
        recs = res.json()["recommendations"]
        self.assertGreaterEqual(len(recs), 16)
        for crop in recs:
            self.assertFalse(crop["suitability_flags"]["affordable"], f"{crop['name']} should be unaffordable")
            self.assertEqual(crop["score_breakdown"]["budget_score"], 0, f"{crop['name']} budget score should be 0")
            self.assertTrue(any("ZERO WORKING CAPITAL" in r for r in crop["risks"]))


if __name__ == "__main__":
    unittest.main()
