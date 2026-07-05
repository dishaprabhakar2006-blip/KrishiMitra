import httpx

def test_profile():
    payload = {
        "name": "Ramu",
        "location": "Pune,Maharashtra",
        "land_size_acres": None,
        "crop_history": None
    }
    try:
        response = httpx.post("http://localhost:8000/api/profile?lang=english", json=payload, timeout=10.0)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    except Exception as e:
        print("Request failed:", str(e))

if __name__ == "__main__":
    test_profile()
