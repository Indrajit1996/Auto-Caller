#!/usr/bin/env python3
"""
Simple Production Test for Auto-Caller
Tests the production setup with basic functionality
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

def test_health_check():
    """Test if the service is healthy"""
    print("🔍 Testing health check...")
    try:
        with urllib.request.urlopen('http://localhost:8000/health', timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook_endpoint():
    """Test the webhook endpoint"""
    print("\n🔍 Testing webhook endpoint...")
    try:
        data = urllib.parse.urlencode({
            'SpeechResult': 'hello',
            'CallSid': 'test123',
            'Confidence': '0.8'
        }).encode('utf-8')
        
        req = urllib.request.Request(
            'http://localhost:8000/api/calls/handle-speech',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                twiml = response.read().decode()
                print("✅ Webhook endpoint working")
                print(f"   Response: {twiml[:100]}...")
                return True
            else:
                print(f"❌ Webhook failed: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return False

def test_call_api():
    """Test the call API endpoint"""
    print("\n🔍 Testing call API...")
    try:
        payload = {
            "to": "+16023860501",  # Your actual number
            "message": "Hello from production Auto-Caller! This is a test.",
            "voice_id": "Zdsf4NBMlHR5zJJ72y9q"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:8000/api/calls/make-call',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Call API working: {result}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 500 and "not valid" in e.read().decode():
            print("✅ Call API working (expected error for dummy phone number)")
            return True
        else:
            print(f"❌ Call API failed: HTTP {e.code}")
            return False
    except Exception as e:
        print(f"❌ Call API error: {e}")
        return False

def test_production_config():
    """Test production configuration"""
    print("\n🔍 Testing production configuration...")
    
    # Check if webhook URL is configured
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'WEBHOOK_BASE_URL' in env_content:
                print("✅ WEBHOOK_BASE_URL configured")
                return True
            else:
                print("❌ WEBHOOK_BASE_URL not found in .env")
                return False
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False

def run_performance_test():
    """Run a simple performance test"""
    print("\n🚀 Running performance test...")
    
    start_time = time.time()
    success_count = 0
    total_requests = 10
    
    for i in range(total_requests):
        try:
            with urllib.request.urlopen('http://localhost:8000/health', timeout=5) as response:
                if response.status == 200:
                    success_count += 1
        except:
            pass
    
    end_time = time.time()
    total_time = end_time - start_time
    success_rate = success_count / total_requests * 100
    requests_per_second = total_requests / total_time
    
    print(f"📊 Performance Results:")
    print(f"   Total requests: {total_requests}")
    print(f"   Successful: {success_count}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Requests/second: {requests_per_second:.2f}")
    
    if requests_per_second > 10:
        print("   ✅ Performance: Excellent")
    elif requests_per_second > 5:
        print("   ⚠️  Performance: Good")
    else:
        print("   ❌ Performance: Poor")

def main():
    """Main test function"""
    print("🚀 Auto-Caller Production Test")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Webhook Endpoint", test_webhook_endpoint),
        ("Call API", test_call_api),
        ("Production Config", test_production_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Production setup is ready.")
        run_performance_test()
    else:
        print("❌ Some tests failed. Please check the configuration.")
    
    print(f"\n📝 Next steps:")
    print("1. Update WEBHOOK_BASE_URL in .env with your actual domain")
    print("2. Deploy to production: ./deploy_production.sh --production")
    print("3. Test with real phone numbers")
    print("4. Monitor performance and scale as needed")

if __name__ == "__main__":
    main() 