"""Enhanced caching with tag-based invalidation for enterprise scalability"""

from django.core.cache import cache
from typing import List, Any, Optional

class TaggedCache:
    """Cache with tag-based invalidation support"""
    
    def __init__(self):
        self.cache = cache
    
    def set_with_tags(self, key: str, value: Any, tags: List[str], timeout: int = 300):
        """Set cache value with associated tags"""
        self.cache.set(key, value, timeout)
        
        for tag in tags:
            self._add_key_to_tag(tag, key)
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return self.cache.get(key)
    
    def invalidate_tag(self, tag: str):
        """Invalidate all keys associated with a tag"""
        keys = self._get_keys_for_tag(tag)
        if keys:
            self.cache.delete_many(keys)
            self._clear_tag(tag)
    
    def _add_key_to_tag(self, tag: str, key: str):
        """Add key to tag set"""
        tag_key = f"tag:{tag}"
        existing_keys = self.cache.get(tag_key, set())
        existing_keys.add(key)
        self.cache.set(tag_key, existing_keys, 86400)
    
    def _get_keys_for_tag(self, tag: str) -> List[str]:
        """Get all keys for a tag"""
        tag_key = f"tag:{tag}"
        keys = self.cache.get(tag_key, set())
        return list(keys)
    
    def _clear_tag(self, tag: str):
        """Clear tag set"""
        tag_key = f"tag:{tag}"
        self.cache.delete(tag_key)

tagged_cache = TaggedCache()