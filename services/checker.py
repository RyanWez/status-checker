"""
Domain health checking service
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import aiohttp
import requests
from utils.timezone import myanmar_now

logger = logging.getLogger(__name__)

class DomainChecker:
    """Handles domain health checking functionality"""
    
    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """Ensure domain has proper protocol"""
        if not domain.startswith(('http://', 'https://')):
            return f'https://{domain}'
        return domain
    
    @staticmethod
    async def check_domain_async(session: aiohttp.ClientSession, domain: str) -> Dict:
        """
        Async check if a domain is accessible
        Returns dict with status, response_time, and timestamp
        """
        normalized_domain = DomainChecker._normalize_domain(domain)
        
        try:
            start_time = datetime.now()
            
            # Use session timeout from parent call
            async with session.get(
                normalized_domain, 
                allow_redirects=True,
                ssl=False  # Skip SSL verification for speed (optional)
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                return {
                    'domain': domain,
                    'status': 'up' if response.status == 200 else 'down',
                    'status_code': response.status,
                    'response_time': response_time,
                    'timestamp': myanmar_now(),
                    'error': None if response.status == 200 else f"HTTP {response.status}"
                }
        except asyncio.TimeoutError:
            return {
                'domain': domain,
                'status': 'down',
                'status_code': None,
                'response_time': None,
                'timestamp': myanmar_now(),
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'domain': domain,
                'status': 'down',
                'status_code': None,
                'response_time': None,
                'timestamp': myanmar_now(),
                'error': str(e)
            }
    
    @staticmethod
    def check_domain_sync(domain: str) -> Dict:
        """
        Synchronous domain check for backward compatibility
        """
        normalized_domain = DomainChecker._normalize_domain(domain)
        
        try:
            start_time = datetime.now()
            response = requests.get(normalized_domain, timeout=10, allow_redirects=True)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            
            return {
                'domain': domain,
                'status': 'up' if response.status_code == 200 else 'down',
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': myanmar_now(),
                'error': None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        except requests.exceptions.Timeout:
            return {
                'domain': domain,
                'status': 'down',
                'status_code': None,
                'response_time': None,
                'timestamp': myanmar_now(),
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'domain': domain,
                'status': 'down',
                'status_code': None,
                'response_time': None,
                'timestamp': myanmar_now(),
                'error': str(e)
            }
    
    @staticmethod
    async def check_multiple_domains(domains: List[str], max_concurrent: int = 50) -> List[Dict]:
        """
        Check multiple domains concurrently with optimized performance for 150+ domains
        """
        if not domains:
            return []
        
        # Optimize for large number of domains
        connector = aiohttp.TCPConnector(
            limit=max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300,  # DNS cache for 5 minutes
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=8,  # Reduced timeout for faster processing
            connect=3,
            sock_read=5
        )
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={'User-Agent': 'Domain-Checker-Bot/1.0'}
        ) as session:
            
            # Process domains in batches for better memory management
            batch_size = 50
            all_results = []
            
            for i in range(0, len(domains), batch_size):
                batch = domains[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(domains)-1)//batch_size + 1} ({len(batch)} domains)")
                
                tasks = [DomainChecker.check_domain_async(session, domain) for domain in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        all_results.append({
                            'domain': batch[j],
                            'status': 'down',
                            'status_code': None,
                            'response_time': None,
                            'timestamp': myanmar_now(),
                            'error': str(result)
                        })
                    else:
                        all_results.append(result)
                
                # Small delay between batches to prevent overwhelming
                if i + batch_size < len(domains):
                    await asyncio.sleep(0.1)
            
            return all_results
    
    @staticmethod
    async def check_domains_by_group(domains_by_group: Dict[str, List[str]], max_concurrent: int = 50) -> Dict[str, List[Dict]]:
        """
        Check domains grouped by group name for better organization
        """
        results_by_group = {}
        
        for group_name, domains in domains_by_group.items():
            if domains:
                logger.info(f"Checking {len(domains)} domains in group '{group_name}'")
                group_results = await DomainChecker.check_multiple_domains(domains, max_concurrent)
                results_by_group[group_name] = group_results
            else:
                results_by_group[group_name] = []
        
        return results_by_group