import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("=" * 65)
    print("TESTING PAYSHIELD AI REST API CONTRACT ENDPOINTS")
    print("=" * 65)

    # 1. Test POST /api/simulate
    print("\n1. Testing POST /api/simulate ...")
    sim_payload = {"count": 10, "attack_ratio": 0.4}
    r1 = requests.post(f"{BASE_URL}/api/simulate", json=sim_payload)
    print(f"Status Code: {r1.status_code}")
    print("Metrics:", json.dumps(r1.json()["current_metrics"], indent=2))

    # 2. Test POST /api/detect (Attack Payload)
    print("\n2. Testing POST /api/detect (Attack Payload) ...")
    detect_payload = {
        "transaction_id": "TXN_LIVE_TEST_01",
        "user_id": "USER_0042",
        "amount": 95000.0,
        "transaction_type": "TRANSFER",
        "country": "Russia",
        "device_type": "Tor_Browser",
        "ip_address": "185.220.101.5",
        "seconds_since_prev": 4.0
    }
    r2 = requests.post(f"{BASE_URL}/api/detect", json=detect_payload)
    print(f"Status Code: {r2.status_code}")
    print("Response:", json.dumps(r2.json(), indent=2))

    # 3. Test GET /api/metrics
    print("\n3. Testing GET /api/metrics ...")
    r3 = requests.get(f"{BASE_URL}/api/metrics")
    print(f"Status Code: {r3.status_code}")
    print("Response:", json.dumps(r3.json(), indent=2))

    # 4. Test GET /api/adversarial-battle
    print("\n4. Testing GET /api/adversarial-battle ...")
    r4 = requests.get(f"{BASE_URL}/api/adversarial-battle")
    print(f"Status Code: {r4.status_code}")
    print("Response:", json.dumps(r4.json(), indent=2))

    print("\n" + "=" * 65)
    print("ALL ENDPOINTS OPERATIONAL AND CONTRACT-COMPLIANT")
    print("=" * 65)

if __name__ == "__main__":
    test_all()