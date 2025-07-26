#!/usr/bin/env python3
"""
Test script for bulk domain addition functionality
"""

import asyncio
from services.database import DatabaseService
from services.checker import DomainChecker
from config.settings import settings

async def test_bulk_addition():
    """Test the new bulk domain addition functionality"""
    print("🧪 Testing Bulk Domain Addition...")
    
    # Initialize database
    db = DatabaseService(settings.MONGO_URL)
    
    # Test domains for bulk addition
    test_domains = [
        "google.com",
        "facebook.com", 
        "github.com",
        "stackoverflow.com",
        "python.org"
    ]
    
    group_name = "TestGroup"
    
    print(f"\n📝 Testing bulk addition of {len(test_domains)} domains to group '{group_name}'...")
    
    # Add domains in bulk
    added_count = 0
    for domain in test_domains:
        if db.add_domain(domain, group_name):
            added_count += 1
            print(f"  ✅ Added {domain}")
        else:
            print(f"  ❌ Failed to add {domain} (may already exist)")
    
    print(f"\n📊 Added {added_count} domains successfully")
    
    # Test concurrent checking
    print(f"\n🔍 Testing concurrent checking of added domains...")
    results = await DomainChecker.check_multiple_domains(test_domains, max_concurrent=10)
    
    # Test bulk status update
    print(f"\n💾 Testing bulk status update...")
    status_updates = [{'domain': r['domain'], 'status_data': r} for r in results]
    updated_count = db.bulk_update_status(status_updates)
    print(f"  Updated {updated_count} domains in bulk")
    
    # Show results
    print(f"\n📈 Results:")
    up_count = sum(1 for r in results if r['status'] == 'up')
    down_count = len(results) - up_count
    print(f"  ✅ UP: {up_count}")
    print(f"  🚨 DOWN: {down_count}")
    
    # Test group summary
    print(f"\n📊 Group summary:")
    summary = db.get_group_summary()
    if group_name in summary:
        stats = summary[group_name]
        print(f"  {group_name}: {stats}")
    
    # Clean up test data
    print(f"\n🧹 Cleaning up test data...")
    for domain in test_domains:
        if db.remove_domain(domain):
            print(f"  Removed {domain}")
    
    db.close()
    print(f"\n✅ Bulk addition test completed!")

if __name__ == '__main__':
    asyncio.run(test_bulk_addition())