import httpx
import json

def test():
    url = "http://localhost:8000/api/chat"
    payload = {
        "query": "What is the current mandi price for tomato in Karnataka?",
        "language": "hindi",
        "image_base64": None
    }
    
    try:
        print("Sending POST request to /api/chat...")
        response = httpx.post(url, json=payload, timeout=30.0)
        print("Status code:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error connecting to server:", str(e))

if __name__ == "__main__":
    test()
