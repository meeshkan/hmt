from entity_extractor import EntityExtractor
from path_analyzer import PathAnalyzer
from entity_extractor import EntityExtractor

analyzer=PathAnalyzer()
extractor = EntityExtractor()


string ='/accounts/v3/accounts/GcfU8g0c_pxJXR8spP3uc4jMXRwalQyIDwj820w8-TY.8vlH6Nvrzd0fFiaSD6U4_Q.hR3Bjufb_ZzypZXU707zJg'
#string1='/v3/profiles/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/borderless-accounts/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/statement.json'

#print(extractor.get_entity_from_url(string))
print(f"path ===================================> {string}")
print(f"entity ==================================> {analyzer.extract_values(string).entity}")
print(f"id ==================================> {analyzer.extract_values(string).id}")
