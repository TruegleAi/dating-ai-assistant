#!/usr/bin/env python3
"""
Test script to verify CORS configuration and API functionality
"""
import requests
import json
import sys
import os

def test_cors_and_api():
    print("🔍 Testing CORS and API functionality...")
    
    # Test if the app is running locally
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Local API is accessible")
        else:
            print(f"❌ Local API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local API. Make sure the app is running on http://localhost:5000")
        print("   Run './start_app.sh' to start the application")
        return False
    except Exception as e:
        print(f"❌ Error connecting to local API: {e}")
        return False

    # Test CORS headers
    try:
        # Make a preflight request (OPTIONS) to check CORS
        headers = {
            'Origin': 'https://example.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'X-Requested-With'
        }
        preflight_response = requests.options("http://localhost:5000/advice", headers=headers, timeout=10)
        
        cors_headers = {
            'Access-Control-Allow-Origin': preflight_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': preflight_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': preflight_response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"📋 CORS Headers from preflight request:")
        for header, value in cors_headers.items():
            print(f"   {header}: {value}")
            
        # Even though FastAPI doesn't typically respond to OPTIONS for POST routes,
        # we can still check if our main endpoints return proper CORS headers
        health_response = requests.get("http://localhost:5000/health", timeout=10)
        origin_header = health_response.headers.get('access-control-allow-origin')
        print(f"   Access-Control-Allow-Origin (from GET /health): {origin_header}")
        
        if origin_header == "*" or origin_header == "https://example.com":
            print("✅ CORS is properly configured to allow cross-origin requests")
        else:
            print("⚠️  CORS might not be properly configured")
            
    except Exception as e:
        print(f"⚠️  Could not test CORS headers: {e}")

    # Test actual API functionality
    try:
        # Test advice endpoint
        advice_payload = {
            "text": "How to start a conversation?",
            "context": ["general dating psychology"],
            "user_type": "free"
        }
        advice_response = requests.post(
            "http://localhost:5000/advice",
            json=advice_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if advice_response.status_code == 200:
            print("✅ Advice endpoint is working correctly")
            data = advice_response.json()
            if 'success' in data:
                print("✅ Response format is correct")
            else:
                print("⚠️  Response format might be unexpected")
        else:
            print(f"❌ Advice endpoint returned status: {advice_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing advice endpoint: {e}")

    # Test interest analysis endpoint
    try:
        analysis_payload = {
            "messages": [
                {"sender": "woman", "text": "Hey! How are you?", "timestamp": "2023-01-01T12:00:00Z"},
                {"sender": "man", "text": "Hi! I'm doing well, thanks for asking!", "timestamp": "2023-01-01T12:05:00Z"},
                {"sender": "woman", "text": "That's great! What do you like to do for fun?", "timestamp": "2023-01-01T12:10:00Z"}
            ]
        }
        analysis_response = requests.post(
            "http://localhost:5000/analyze",
            json=analysis_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if analysis_response.status_code == 200:
            print("✅ Interest analysis endpoint is working correctly")
        else:
            print(f"❌ Interest analysis endpoint returned status: {analysis_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing analysis endpoint: {e}")

    print("\n🎯 Testing completed!")
    return True

if __name__ == "__main__":
    test_cors_and_api()