#!/usr/bin/env python3
"""
Load Testing Script for Auto-Caller Production Setup
Tests the system with realistic load for 300k users
"""

import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime
import statistics

class LoadTester:
    def __init__(self, base_url="http://localhost:8000", max_concurrent=100, test_duration=300):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.test_duration = test_duration
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    async def make_call_request(self, session, call_id):
        """Make a single call request"""
        start_time = time.time()
        try:
            payload = {
                "to_number": f"+1{random.randint(1000000000, 9999999999)}",
                "message": f"Load test call {call_id} - Hello from the automated caller system!",
                "voice_id": "Zdsf4NBMlHR5zJJ72y9q"
            }
            
            async with session.post(
                f"{self.base_url}/api/calls/make-call",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    self.results.append({
                        "call_id": call_id,
                        "response_time": response_time,
                        "status": response.status,
                        "success": result.get("success", False),
                        "call_sid": result.get("call_sid"),
                        "timestamp": datetime.now().isoformat()
                    })
                    return True
                else:
                    self.errors.append({
                        "call_id": call_id,
                        "response_time": response_time,
                        "status": response.status,
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    })
                    return False
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.errors.append({
                "call_id": call_id,
                "response_time": response_time,
                "status": "EXCEPTION",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def health_check(self, session):
        """Check if the service is healthy"""
        try:
            async with session.get(f"{self.base_url}/health", timeout=10) as response:
                return response.status == 200
        except:
            return False
    
    async def run_load_test(self):
        """Run the main load test"""
        print(f"🚀 Starting Load Test for 300k Users")
        print(f"   Base URL: {self.base_url}")
        print(f"   Max Concurrent: {self.max_concurrent}")
        print(f"   Duration: {self.test_duration} seconds")
        print(f"   Target: {self.max_concurrent * (self.test_duration // 60)} calls per minute")
        print()
        
        self.start_time = time.time()
        
        # Check if service is healthy
        async with aiohttp.ClientSession() as session:
            if not await self.health_check(session):
                print("❌ Service is not healthy. Aborting load test.")
                return
        
        # Run load test
        call_id = 0
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - self.start_time < self.test_duration:
                # Create new tasks up to max_concurrent
                while len(tasks) < self.max_concurrent:
                    call_id += 1
                    task = asyncio.create_task(self.make_call_request(session, call_id))
                    tasks.append(task)
                
                # Wait for some tasks to complete
                if tasks:
                    done, pending = await asyncio.wait(tasks, timeout=1.0)
                    tasks = list(pending)
                    
                    # Print progress
                    if call_id % 50 == 0:
                        elapsed = time.time() - self.start_time
                        success_rate = len([r for r in self.results if r["success"]]) / max(len(self.results), 1) * 100
                        print(f"📊 Progress: {call_id} calls, {elapsed:.1f}s elapsed, {success_rate:.1f}% success rate")
        
        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = time.time()
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        total_time = self.end_time - self.start_time
        total_calls = len(self.results) + len(self.errors)
        successful_calls = len([r for r in self.results if r["success"]])
        failed_calls = len(self.errors) + len([r for r in self.results if not r["success"]])
        
        if self.results:
            response_times = [r["response_time"] for r in self.results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        calls_per_second = total_calls / total_time if total_time > 0 else 0
        calls_per_minute = calls_per_second * 60
        
        print("\n" + "="*60)
        print("📊 LOAD TEST REPORT")
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
        print(f"   99th Percentile: {p99_response_time:.3f}s")
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
                "p95_response_time": p95_response_time,
                "p99_response_time": p99_response_time
            },
            "results": self.results,
            "errors": self.errors
        }
        
        with open(f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

async def main():
    """Main function to run the load test"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test the Auto-Caller API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--concurrent", type=int, default=50, help="Maximum concurrent requests")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = LoadTester(
        base_url=args.url,
        max_concurrent=args.concurrent,
        test_duration=args.duration
    )
    
    await tester.run_load_test()
    tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main()) 