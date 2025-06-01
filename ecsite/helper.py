import logging
import hashlib

from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('ecsite')


def log_single_change(model_ref, new_values, old_values):
    changed_fields = [field for field in old_values if old_values[field] != new_values[field]]
    if changed_fields:
        logger.info(f"Model {model_ref.__class__.__name__} with id={model_ref.pk} updated. Changed fields: {changed_fields}. Old values: {old_values}. New values: {new_values}")

def log_single_create(model_ref, new_values):
    logger.info(f"Model {model_ref.__class__.__name__} with id={model_ref.pk} created: {new_values}")

def idempontent(username, obj) -> bool:
    key = hashlib.blake2b(
            f"{username}, {obj}".encode("utf-8")
        ).hexdigest()
    is_cached = cache.get(key)

    if is_cached:
        return True

    expiary  = 60*60*3 # 3 hours 
    cache.set(key, 'True' , expiary)

    return False
