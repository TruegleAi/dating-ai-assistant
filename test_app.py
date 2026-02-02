#!/usr/bin/env python3
"""
Test Script for Dating AI Assistant
User: Duck E. Duck (therealduckyduck@gmail.com)
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_advice():
    """Test advice endpoint with real user scenario"""
    print("\n" + "="*60)
    print("Testing Dating Advice Endpoint")
    print("="*60)
    payload = {
        "text": "She replied to my message after 2 days. Should I respond right away?",
        "context": ["Push-Pull Dynamics", "Qualification techniques"],
        "user_type": "premium"
    }
    response = requests.post(f"{BASE_URL}/advice", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Query: {payload['text']}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nAdvice: {data['data']['response']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_interest_analysis():
    """Test interest analysis with sample conversation"""
    print("\n" + "="*60)
    print("Testing Interest Analysis Endpoint")
    print("="*60)
    payload = {
        "messages": [
            {"sender": "user", "text": "Hey, how's your week going?"},
            {"sender": "woman", "text": "Pretty good! Just been busy with work"},
            {"sender": "user", "text": "What do you do?"},
            {"sender": "woman", "text": "I'm in marketing. What about you? 😊"},
            {"sender": "user", "text": "I work in tech"},
            {"sender": "woman", "text": "That's cool! What kind of projects do you work on?"}
        ]
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        analysis = data['analysis']
        print(f"\nInterest Score: {analysis['score']}/100")
        print(f"Interest Level: {analysis['level']}")
        print(f"Advice: {analysis['advice']}")
        print(f"Suggested Reply Time: {analysis['reply_time']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_opener_generator():
    """Test premium opener generator"""
    print("\n" + "="*60)
    print("Testing Opener Generator Endpoint")
    print("="*60)
    payload = {
        "profile_context": "She has photos of hiking and loves dogs",
        "platform": "instagram"
    }
    response = requests.post(f"{BASE_URL}/opener", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Profile Context: {payload['profile_context']}")
    if response.status_code == 200:
        data = response.json()
        opener_data = data['opener']
        print(f"\nOpening Line: {opener_data['opener']}")
        print(f"Technique: {opener_data['technique']}")
        print(f"Expected Success: {opener_data['success_rate']}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("DATING AI ASSISTANT - TEST SUITE")
    print(f"User: Duck E. Duck (therealduckyduck@gmail.com)")
    print("="*70)

    results = {
        "Health Check": test_health(),
        "Dating Advice": test_advice(),
        "Interest Analysis": test_interest_analysis(),
        "Opener Generator": test_opener_generator()
    }

    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The app is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("="*70 + "\n")

    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("Make sure the app is running: python3 app.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
