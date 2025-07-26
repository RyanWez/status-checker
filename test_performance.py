#!/usr/bin/env python3
"""
Performance test for 150+ domains
"""

import asyncio
import time
from services.checker import DomainChecker

async def test_performance():
    """Test performance with 150+ domains"""
    print("⚡ Performance Test for 150+ Domains")
    
    # Generate test domains (mix of real and fake for testing)
    test_domains = []
    
    # Add some real domains
    real_domains = [
        "google.com", "facebook.com", "github.com", "stackoverflow.com",
        "python.org", "django.org", "flask.org", "fastapi.tiangolo.com",
        "docs.python.org", "pypi.org", "numpy.org", "pandas.pydata.org",
        "matplotlib.org", "scipy.org", "scikit-learn.org", "tensorflow.org",
        "pytorch.org", "jupyter.org", "anaconda.org", "conda.io"
    ]
    
    # Generate more test domains to reach 150+
    for i in range(1, 131):  # 130 more to make 150 total
        test_domains.append(f"test-domain-{i:03d}.example.com")
    
    test_domains.extend(real_domains)
    
    print(f"📊 Testing with {len(test_domains)} domains")
    
    # Test different concurrency levels
    concurrency_levels = [10, 25, 50, 100, 150]
    
    for max_concurrent in concurrency_levels:
        print(f"\n🔄 Testing with max_concurrent={max_concurrent}")
        
        start_time = time.time()
        results = await DomainChecker.check_multiple_domains(test_domains, max_concurrent)
        end_time = time.time()
        
        duration = end_time - start_time
        up_count = sum(1 for r in results if r['status'] == 'up')
        down_count = len(results) - up_count
        
        print(f"  ⏱️  Duration: {duration:.2f} seconds")
        print(f"  📈 Rate: {len(results)/duration:.1f} domains/second")
        print(f"  ✅ UP: {up_count}, 🚨 DOWN: {down_count}")
        print(f"  🎯 Avg time per domain: {duration/len(results):.3f}s")

    print("\n🏆 Performance test completed!")

if __name__ == '__main__':
    asyncio.run(test_performance())