#!/usr/bin/env python3
"""
Simple Load Testing Script for Auto-Caller Production Setup
Uses only standard library modules
"""

import requests
import time
import json
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class SimpleLoadTester:
    def __init__(self, base_url="http://localhost:8000", max_concurrent=10, test_duration=30):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.test_duration = test_duration
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
        
    def make_call_request(self, call_id):
        """Make a single call request"""
        start_time = time.time()
        try:
            payload = {
                "to": f"+1{random.randint(1000000000, 9999999999)}",
                "message": f"Load test call {call_id} - Hello from the automated caller system!",
                "voice_id": "Zdsf4NBMlHR5zJJ72y9q"
            }
            
            response = requests.post(
                f"{self.base_url}/api/calls/make-call",
                json=payload,
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            with self.lock:
                if response.status_code == 200:
                    result = response.json()
                    self.results.append({
                        "call_id": call_id,
                        "response_time": response_time,
                        "status": response.status_code,
                        "success": "status" in result and result["status"] == "initiated",
                        "call_sid": result.get("call_sid"),
                        "timestamp": datetime.now().isoformat()
                    })
                    return True
                else:
                    self.errors.append({
                        "call_id": call_id,
                        "response_time": response_time,
                        "status": response.status_code,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.now().isoformat()
                    })
                    return False
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            with self.lock:
                self.errors.append({
                    "call_id": call_id,
                    "response_time": response_time,
                    "status": "EXCEPTION",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            return False
    
    def health_check(self):
        """Check if the service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def run_load_test(self):
        """Run the main load test"""
        print(f"🚀 Starting Simple Load Test for 300k Users")
        print(f"   Base URL: {self.base_url}")
        print(f"   Max Concurrent: {self.max_concurrent}")
        print(f"   Duration: {self.test_duration} seconds")
        print()
        
        self.start_time = time.time()
        
        # Check if service is healthy
        if not self.health_check():
            print("❌ Service is not healthy. Aborting load test.")
            return
        
        print("✅ Service is healthy. Starting load test...")
        
        # Run load test with thread pool
        call_id = 0
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = []
            
            while time.time() - self.start_time < self.test_duration:
                # Submit new tasks up to max_concurrent
                while len(futures) < self.max_concurrent:
                    call_id += 1
                    future = executor.submit(self.make_call_request, call_id)
                    futures.append(future)
                
                # Wait for some tasks to complete
                done_futures = []
                for future in futures:
                    if future.done():
                        done_futures.append(future)
                
                for future in done_futures:
                    futures.remove(future)
                
                # Print progress
                if call_id % 20 == 0:
                    elapsed = time.time() - self.start_time
                    success_count = len([r for r in self.results if r["success"]])
                    total_completed = len(self.results) + len(self.errors)
                    success_rate = success_count / max(total_completed, 1) * 100
                    print(f"📊 Progress: {call_id} calls submitted, {elapsed:.1f}s elapsed, {success_rate:.1f}% success rate")
                
                time.sleep(0.1)  # Small delay to prevent overwhelming
            
            # Wait for remaining tasks
            for future in futures:
                future.result()
        
        self.end_time = time.time()
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        total_time = self.end_time - self.start_time
        total_calls = len(self.results) + len(self.errors)
        successful_calls = len([r for r in self.results if r["success"]])
        failed_calls = len(self.errors) + len([r for r in self.results if not r["success"]])
        
        if self.results:
            response_times = [r["response_time"] for r in self.results]
            avg_response_time = sum(response_times) / len(response_times)
            median_response_time = sorted(response_times)[len(response_times) // 2]
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = median_response_time = p95_response_time = 0
        
        calls_per_second = total_calls / total_time if total_time > 0 else 0
        calls_per_minute = calls_per_second * 60
        
        print("\n" + "="*60)
        print("📊 SIMPLE LOAD TEST REPORT")
        print("="*60)
        print(f"⏱️  Test Duration: {total_time:.2f} seconds")
        print(f"📞 Total Calls: {total_calls}")
        print(f"✅ Successful Calls: {successful_calls}")
        print(f"❌ Failed Calls: {failed_calls}")
        print(f"📈 Success Rate: {successful_calls/total_calls*100:.2f}%" if total_calls > 0 else "📈 Success Rate: 0%")
        print(f"🚀 Throughput: {calls_per_second:.2f} calls/second ({calls_per_minute:.0f} calls/minute)")
        print()
        
        print("⏱️  Response Times:")
        print(f"   Average: {avg_response_time:.3f}s")
        print(f"   Median: {median_response_time:.3f}s")
        print(f"   95th Percentile: {p95_response_time:.3f}s")
        print()
        
        if self.errors:
            print("❌ Error Summary:")
            error_types = {}
            for error in self.errors:
                error_type = error["error"]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count} occurrences")
            print()
        
        # Performance assessment
        print("🎯 Performance Assessment:")
        if calls_per_minute >= 1000:
            print("   ✅ Excellent: Can handle 300k users")
        elif calls_per_minute >= 500:
            print("   ⚠️  Good: May need scaling for 300k users")
        elif calls_per_minute >= 100:
            print("   ❌ Poor: Significant scaling needed for 300k users")
        else:
            print("   ❌ Critical: Major performance issues")
        
        if avg_response_time < 2:
            print("   ✅ Response time: Excellent")
        elif avg_response_time < 5:
            print("   ⚠️  Response time: Acceptable")
        else:
            print("   ❌ Response time: Too slow")
        
        if successful_calls/total_calls >= 0.99:
            print("   ✅ Reliability: Excellent")
        elif successful_calls/total_calls >= 0.95:
            print("   ⚠️  Reliability: Good")
        else:
            print("   ❌ Reliability: Poor")
        
        print("\n" + "="*60)
        
        # Save detailed results
        report_data = {
            "test_config": {
                "base_url": self.base_url,
                "max_concurrent": self.max_concurrent,
                "test_duration": self.test_duration
            },
            "summary": {
                "total_time": total_time,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": successful_calls/total_calls if total_calls > 0 else 0,
                "calls_per_second": calls_per_second,
                "calls_per_minute": calls_per_minute,
                "avg_response_time": avg_response_time,
                "median_response_time": median_response_time,
                "p95_response_time": p95_response_time
            },
            "results": self.results,
            "errors": self.errors
        }
        
        filename = f"simple_load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: {filename}")

def main():
    """Main function to run the load test"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple load test the Auto-Caller API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--concurrent", type=int, default=10, help="Maximum concurrent requests")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = SimpleLoadTester(
        base_url=args.url,
        max_concurrent=args.concurrent,
        test_duration=args.duration
    )
    
    tester.run_load_test()
    tester.generate_report()

if __name__ == "__main__":
    main() 