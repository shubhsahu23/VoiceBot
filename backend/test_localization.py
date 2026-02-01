import sys, os
# Ensure project root is on sys.path so 'backend' package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services import bedrock_service as b

print("ISO -> Marathi:", b.localize_dates_in_text("तुमचे सदस्यत्व 2026-02-01 रोजी संपते", "Marathi"))
print("DMY -> Marathi:", b.localize_dates_in_text("शेवटचा स्वॅप 01/02/2026", "Marathi"))
print("Digits -> Marathi:", b.localize_number("2026", "Marathi"))
s = "माझा ड्रायव्हर आयडी DRV003 आहे"
import re
print("Devanagari found:", bool(re.search(r'[\u0900-\u097F]', s)))
marathi_tokens = ['आहे','मला','कृपया','सदस्यत्व','शेवट','शेवटचा','ड्रायव्हर','नाव','स्वॅप','कधी','नवीन']
print("Has marathi token:", any(tok in s for tok in marathi_tokens))
