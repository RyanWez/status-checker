#!/usr/bin/env python3
"""
Migration script to organize existing domains into groups
"""

from services.database import DatabaseService
from config.settings import settings

def migrate_domains_to_groups():
    """Interactive script to organize domains into groups"""
    print("🔄 Domain Group Migration Tool")
    print("=" * 40)
    
    # Initialize database
    db = DatabaseService(settings.MONGO_URL)
    
    # Get all domains
    domains = db.get_all_domains()
    
    if not domains:
        print("📝 No domains found to migrate.")
        return
    
    print(f"📊 Found {len(domains)} domains to organize")
    
    # Show current domains
    print("\n📋 Current domains:")
    for i, domain_doc in enumerate(domains, 1):
        domain = domain_doc['domain']
        current_group = domain_doc.get('group_name', 'Default')
        status = domain_doc.get('last_status', 'unknown')
        status_emoji = {'up': '✅', 'down': '🚨', 'unknown': '⚪'}.get(status, '⚪')
        print(f"  {i:3d}. {status_emoji} {domain} (Group: {current_group})")
    
    print("\n" + "=" * 40)
    print("Migration Options:")
    print("1. Auto-organize by domain patterns")
    print("2. Manual group assignment")
    print("3. Bulk assign to single group")
    print("4. Exit without changes")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        auto_organize_domains(db, domains)
    elif choice == "2":
        manual_group_assignment(db, domains)
    elif choice == "3":
        bulk_assign_group(db, domains)
    elif choice == "4":
        print("👋 Exiting without changes.")
    else:
        print("❌ Invalid choice.")
    
    db.close()

def auto_organize_domains(db, domains):
    """Auto-organize domains based on patterns"""
    print("\n🤖 Auto-organizing domains...")
    
    # Define patterns and their groups
    patterns = {
        'api': 'API',
        'cdn': 'CDN',
        'www': 'Web',
        'app': 'Application',
        'admin': 'Admin',
        'blog': 'Blog',
        'shop': 'Shop',
        'mail': 'Email',
        'ftp': 'FTP',
        'test': 'Testing',
        'dev': 'Development',
        'staging': 'Staging',
        'prod': 'Production'
    }
    
    updated_count = 0
    
    for domain_doc in domains:
        domain = domain_doc['domain']
        current_group = domain_doc.get('group_name', 'Default')
        
        # Skip if already in a non-default group
        if current_group != 'Default':
            continue
        
        # Check patterns
        new_group = None
        for pattern, group in patterns.items():
            if pattern in domain.lower():
                new_group = group
                break
        
        # If no pattern matches, assign based on domain length or other criteria
        if not new_group:
            if len(domain) < 15:
                new_group = 'Web1'
            elif len(domain) < 25:
                new_group = 'Web2'
            else:
                new_group = 'Web3'
        
        # Update domain group
        if db.update_domain_group(domain, new_group):
            print(f"  ✅ {domain} -> {new_group}")
            updated_count += 1
        else:
            print(f"  ❌ Failed to update {domain}")
    
    print(f"\n🎉 Auto-organized {updated_count} domains!")

def manual_group_assignment(db, domains):
    """Manual group assignment for each domain"""
    print("\n✏️  Manual group assignment")
    print("Enter group name for each domain (or press Enter to keep current):")
    
    updated_count = 0
    
    for domain_doc in domains:
        domain = domain_doc['domain']
        current_group = domain_doc.get('group_name', 'Default')
        
        new_group = input(f"  {domain} (current: {current_group}) -> ").strip()
        
        if new_group and new_group != current_group:
            if db.update_domain_group(domain, new_group):
                print(f"    ✅ Updated to {new_group}")
                updated_count += 1
            else:
                print(f"    ❌ Failed to update")
    
    print(f"\n🎉 Manually updated {updated_count} domains!")

def bulk_assign_group(db, domains):
    """Bulk assign all domains to a single group"""
    print("\n📦 Bulk group assignment")
    
    group_name = input("Enter group name for all domains: ").strip()
    
    if not group_name:
        print("❌ Group name cannot be empty.")
        return
    
    print(f"\n🔄 Assigning all domains to '{group_name}'...")
    
    updated_count = 0
    
    for domain_doc in domains:
        domain = domain_doc['domain']
        
        if db.update_domain_group(domain, group_name):
            updated_count += 1
        else:
            print(f"  ❌ Failed to update {domain}")
    
    print(f"\n🎉 Bulk assigned {updated_count} domains to '{group_name}'!")

if __name__ == '__main__':
    try:
        migrate_domains_to_groups()
    except KeyboardInterrupt:
        print("\n\n👋 Migration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Migration error: {e}")