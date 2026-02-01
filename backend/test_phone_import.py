import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services import mongo_service as m
print('verify_phone available:', hasattr(m, 'verify_phone'))
print('get_driver_by_phone available:', hasattr(m, 'get_driver_by_phone'))
print('Sample normalized:', m._normalize_phone('+91 98765-43210'))
