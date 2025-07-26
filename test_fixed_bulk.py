#!/usr/bin/env python3
"""
Test script for the fixed bulk domain addition
"""

import asyncio
from services.database import DatabaseService
from services.checker import DomainChecker
from config.settings import settings

async def test_fixed_bulk_addition():
    """Test the fixed bulk domain addition functionality"""
    print("🧪 Testing Fixed Bulk Domain Addition...")
    
    # Initialize database
    db = DatabaseService(settings.MONGO_URL)
    
    # Test domains - mix of valid, invalid, and duplicates
    test_domains = [
        "google.com",
        "facebook.com", 
        "github.com",
        "invalid-domain",  # Invalid
        "stackoverflow.com",
        "python.org",
        "google.com"  # Duplicate
    ]
    
    group_name = "TestBulk"
    
    print(f"\n📝 Testing bulk addition with {len(test_domains)} domains:")
    print(f"   Domains: {', '.join(test_domains)}")
    print(f"   Group: {group_name}")
    
    # Test the improved bulk_add_domains method
    print(f"\n🔄 Running bulk_add_domains...")
    result = db.bulk_add_domains(test_domains, group_name)
    
    print(f"\n📊 Results:")
    print(f"   ✅ Added: {len(result['added'])} domains")
    print(f"      {result['added']}")
    print(f"   ⚠️  Existing: {len(result['existing'])} domains")
    print(f"      {result['existing']}")
    print(f"   📍 Same group: {len(result.get('existing_same_group', []))} domains")
    print(f"      {result.get('existing_same_group', [])}")
    print(f"   🔄 Other groups: {len(result.get('existing_other_groups', []))} domains")
    print(f"      {result.get('existing_other_groups', [])}")
    
    # Test concurrent checking of added domains
    if result['added']:
        print(f"\n🔍 Testing concurrent checking of {len(result['added'])} added domains...")
        check_results = await DomainChecker.check_multiple_domains(result['added'], max_concurrent=10)
        
        up_count = sum(1 for r in check_results if r['status'] == 'up')
        down_count = len(check_results) - up_count
        
        print(f"   Check results: ✅ {up_count} UP, 🚨 {down_count} DOWN")
        
        # Test bulk status update
        print(f"\n💾 Testing bulk status update...")
        status_updates = [{'domain': r['domain'], 'status_data': r} for r in check_results]
        updated_count = db.bulk_update_status(status_updates)
        print(f"   Updated {updated_count} domains in database")
    
    # Test adding the same domains again (should all be existing)
    print(f"\n🔄 Testing duplicate detection (adding same domains again)...")
    duplicate_result = db.bulk_add_domains(test_domains, group_name)
    
    print(f"   ✅ Added: {len(duplicate_result['added'])} (should be 0)")
    print(f"   ⚠️  Existing same group: {len(duplicate_result.get('existing_same_group', []))}")
    print(f"   🔄 Existing other groups: {len(duplicate_result.get('existing_other_groups', []))}")
    
    # Test adding to different group
    print(f"\n🔄 Testing cross-group duplicate detection...")
    cross_group_result = db.bulk_add_domains(["google.com", "newdomain.com"], "DifferentGroup")
    
    print(f"   ✅ Added: {len(cross_group_result['added'])} (should be 1 - newdomain.com)")
    print(f"   🔄 Other groups: {cross_group_result.get('existing_other_groups', [])}")
    
    # Clean up test data
    print(f"\n🧹 Cleaning up test data...")
    all_test_domains = test_domains + ["newdomain.com"]
    for domain in all_test_domains:
        if db.remove_domain(domain):
            print(f"   Removed {domain}")
    
    db.close()
    print(f"\n✅ Fixed bulk addition test completed!")

if __name__ == '__main__':
    asyncio.run(test_fixed_bulk_addition())