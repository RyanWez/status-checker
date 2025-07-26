#!/usr/bin/env python3
"""
Test script for group functionality
"""

import asyncio
from services.database import DatabaseService
from services.checker import DomainChecker
from config.settings import settings

async def test_group_functionality():
    """Test the new group-based functionality"""
    print("🧪 Testing Group Functionality...")
    
    # Initialize database
    db = DatabaseService(settings.MONGO_URL)
    
    # Test adding domains to different groups
    test_domains = [
        ("google.com", "Web1"),
        ("facebook.com", "Web1"),
        ("github.com", "Web2"),
        ("stackoverflow.com", "Web2"),
        ("python.org", "Web3"),
        ("django.org", "Web3")
    ]
    
    print("\n📝 Adding test domains to groups...")
    for domain, group in test_domains:
        result = db.add_domain(domain, group)
        print(f"  {'✅' if result else '❌'} {domain} -> {group}")
    
    # Test getting groups
    print("\n📂 Getting groups...")
    groups = db.get_groups()
    print(f"  Groups found: {groups}")
    
    # Test group summary
    print("\n📊 Group summary...")
    summary = db.get_group_summary()
    for group, stats in summary.items():
        print(f"  {group}: {stats}")
    
    # Test checking domains by group
    print("\n🔍 Testing group-based checking...")
    domains_by_group = {}
    for group in groups:
        group_domains = db.get_domains_by_group(group)
        domains_by_group[group] = [d['domain'] for d in group_domains]
        print(f"  {group}: {len(group_domains)} domains")
    
    # Test concurrent checking
    print("\n⚡ Testing optimized concurrent checking...")
    results_by_group = await DomainChecker.check_domains_by_group(domains_by_group, max_concurrent=10)
    
    for group, results in results_by_group.items():
        up_count = sum(1 for r in results if r['status'] == 'up')
        down_count = len(results) - up_count
        print(f"  {group}: ✅{up_count} 🚨{down_count}")
    
    # Test bulk update
    print("\n💾 Testing bulk database update...")
    all_updates = []
    for group_results in results_by_group.values():
        for result in group_results:
            all_updates.append({'domain': result['domain'], 'status_data': result})
    
    updated_count = db.bulk_update_status(all_updates)
    print(f"  Updated {updated_count} domains in bulk")
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    for domain, _ in test_domains:
        db.remove_domain(domain)
        print(f"  Removed {domain}")
    
    db.close()
    print("\n✅ Group functionality test completed!")

if __name__ == '__main__':
    asyncio.run(test_group_functionality())