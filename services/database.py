"""
Database service for MongoDB operations
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from utils.timezone import myanmar_now

logger = logging.getLogger(__name__)

class DatabaseService:
    """Handles all MongoDB operations for domain management"""
    
    def __init__(self, mongo_url: str):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.domains_collection: Optional[Collection] = None
        self.mongo_url = mongo_url
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client.domain_checker
            self.domains_collection = self.db.domains
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def add_domain(self, domain: str, group_name: str = "Default") -> bool:
        """Add a new domain to monitoring with group support"""
        try:
            # Check if domain already exists
            if self.domains_collection.find_one({'domain': domain}):
                return False
            
            domain_doc = {
                'domain': domain,
                'group_name': group_name,
                'added_at': myanmar_now(),
                'last_status': None,
                'last_checked': None,
                'last_response_time': None,
                'last_status_code': None,
                'last_error': None
            }
            self.domains_collection.insert_one(domain_doc)
            logger.info(f"Added domain to monitoring: {domain} (Group: {group_name})")
            return True
        except Exception as e:
            logger.error(f"Error adding domain {domain}: {e}")
            return False
    
    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from monitoring"""
        try:
            result = self.domains_collection.delete_one({'domain': domain})
            if result.deleted_count > 0:
                logger.info(f"Removed domain from monitoring: {domain}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing domain {domain}: {e}")
            return False
    
    def get_all_domains(self) -> List[Dict]:
        """Get all monitored domains"""
        try:
            return list(self.domains_collection.find())
        except Exception as e:
            logger.error(f"Error fetching domains: {e}")
            return []
    
    def get_domain(self, domain: str) -> Optional[Dict]:
        """Get a specific domain"""
        try:
            return self.domains_collection.find_one({'domain': domain})
        except Exception as e:
            logger.error(f"Error fetching domain {domain}: {e}")
            return None
    
    def update_domain_status(self, domain: str, status_data: Dict):
        """Update domain status in database"""
        try:
            self.domains_collection.update_one(
                {'domain': domain},
                {
                    '$set': {
                        'last_status': status_data['status'],
                        'last_checked': status_data['timestamp'],
                        'last_response_time': status_data['response_time'],
                        'last_status_code': status_data['status_code'],
                        'last_error': status_data['error']
                    }
                }
            )
            logger.debug(f"Updated status for domain {domain}: {status_data['status']}")
        except Exception as e:
            logger.error(f"Error updating domain status {domain}: {e}")
    
    def get_domains_count(self) -> int:
        """Get total number of monitored domains"""
        try:
            return self.domains_collection.count_documents({})
        except Exception as e:
            logger.error(f"Error counting domains: {e}")
            return 0
    
    def get_groups(self) -> List[str]:
        """Get all unique group names"""
        try:
            groups = self.domains_collection.distinct('group_name')
            return sorted(groups) if groups else ['Default']
        except Exception as e:
            logger.error(f"Error fetching groups: {e}")
            return ['Default']
    
    def get_domains_by_group(self, group_name: str) -> List[Dict]:
        """Get all domains in a specific group"""
        try:
            return list(self.domains_collection.find({'group_name': group_name}))
        except Exception as e:
            logger.error(f"Error fetching domains for group {group_name}: {e}")
            return []
    
    def get_group_summary(self) -> Dict[str, Dict]:
        """Get summary statistics for each group"""
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': '$group_name',
                        'total': {'$sum': 1},
                        'up': {'$sum': {'$cond': [{'$eq': ['$last_status', 'up']}, 1, 0]}},
                        'down': {'$sum': {'$cond': [{'$eq': ['$last_status', 'down']}, 1, 0]}},
                        'unknown': {'$sum': {'$cond': [{'$eq': ['$last_status', None]}, 1, 0]}}
                    }
                }
            ]
            
            results = list(self.domains_collection.aggregate(pipeline))
            summary = {}
            
            for result in results:
                group_name = result['_id'] or 'Default'
                summary[group_name] = {
                    'total': result['total'],
                    'up': result['up'],
                    'down': result['down'],
                    'unknown': result['unknown']
                }
            
            return summary
        except Exception as e:
            logger.error(f"Error getting group summary: {e}")
            return {}
    
    def update_domain_group(self, domain: str, new_group: str) -> bool:
        """Update domain's group"""
        try:
            result = self.domains_collection.update_one(
                {'domain': domain},
                {'$set': {'group_name': new_group}}
            )
            if result.modified_count > 0:
                logger.info(f"Updated domain {domain} to group {new_group}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating domain group {domain}: {e}")
            return False
    
    def bulk_update_status(self, status_updates: List[Dict]):
        """Bulk update domain statuses for better performance"""
        try:
            from pymongo import UpdateOne
            
            operations = []
            for update_data in status_updates:
                domain = update_data['domain']
                status_data = update_data['status_data']
                
                operations.append(
                    UpdateOne(
                        {'domain': domain},
                        {
                            '$set': {
                                'last_status': status_data['status'],
                                'last_checked': status_data['timestamp'],
                                'last_response_time': status_data['response_time'],
                                'last_status_code': status_data['status_code'],
                                'last_error': status_data['error']
                            }
                        }
                    )
                )
            
            if operations:
                result = self.domains_collection.bulk_write(operations)
                logger.info(f"Bulk updated {result.modified_count} domains")
                return result.modified_count
            return 0
        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            return 0
    
    def bulk_add_domains(self, domains: List[str], group_name: str = "Default") -> Dict[str, List[str]]:
        """Bulk add multiple domains to monitoring with detailed duplicate handling"""
        try:
            added_domains = []
            existing_domains = []
            existing_in_same_group = []
            existing_in_other_groups = []
            
            # Check which domains already exist and in which groups
            existing_docs = list(self.domains_collection.find(
                {'domain': {'$in': domains}}, 
                {'domain': 1, 'group_name': 1}
            ))
            
            existing_domain_info = {doc['domain']: doc['group_name'] for doc in existing_docs}
            
            # Prepare documents for new domains
            new_domain_docs = []
            for domain in domains:
                if domain not in existing_domain_info:
                    # Domain doesn't exist, add it
                    new_domain_docs.append({
                        'domain': domain,
                        'group_name': group_name,
                        'added_at': myanmar_now(),
                        'last_status': None,
                        'last_checked': None,
                        'last_response_time': None,
                        'last_status_code': None,
                        'last_error': None
                    })
                    added_domains.append(domain)
                else:
                    # Domain exists, check which group
                    existing_group = existing_domain_info[domain]
                    existing_domains.append(domain)
                    
                    if existing_group == group_name:
                        existing_in_same_group.append(domain)
                    else:
                        existing_in_other_groups.append(f"{domain} (in {existing_group})")
            
            # Insert new domains in bulk
            if new_domain_docs:
                self.domains_collection.insert_many(new_domain_docs)
                logger.info(f"Bulk added {len(new_domain_docs)} domains to group {group_name}")
            
            return {
                'added': added_domains,
                'existing': existing_domains,
                'existing_same_group': existing_in_same_group,
                'existing_other_groups': existing_in_other_groups
            }
            
        except Exception as e:
            logger.error(f"Error in bulk add domains: {e}")
            return {
                'added': [], 
                'existing': domains,
                'existing_same_group': [],
                'existing_other_groups': []
            }
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")