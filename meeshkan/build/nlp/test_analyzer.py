from entity_extractor import EntityExtractor
from path_analyzer import PathAnalyzer
from entity_extractor import EntityExtractor
#from path_analyzer import PathItem


def test_github():
    analyzer=PathAnalyzer()
    path_item = analyzer.extract_values('/search/users') 
    assert 'user' == path_item.entity
    assert  path_item.id is None


def test_opbank():
    analyzer=PathAnalyzer()
    
    path_item1 = analyzer.extract_values('/v1/payments/confirm')
    assert 'payment' == path_item1.entity
    assert  path_item1.id is None
    
    path_item2 = analyzer.extract_values('/accounts/v3/accounts/GcfU8g0c_pxJXR8spP3uc4jMXRwalQyIDwj820w8-TY.8vlH6Nvrzd0fFiaSD6U4_Q.hR3Bjufb_ZzypZXU707zJg')
    assert 'account' == path_item2.entity
    assert  'GcfU8g0c_pxJXR8spP3uc4jMXRwalQyIDwj820w8-TY.8vlH6Nvrzd0fFiaSD6U4_Q.hR3Bjufb_ZzypZXU707zJg' == path_item2.id 
    


def test_transferwise():
    analyzer=PathAnalyzer()
    
    path_item1 = analyzer.extract_values('/v3/profiles/saf45gdrg4gsdf/transfers/sdfsr456ygh56ujhgf/payments')
    assert 'payment' == path_item1.entity
    assert  'sdfsr456ygh56ujhgf'== path_item1.id # TODO change it because it is not id for payment 
    
    path_item2 = analyzer.extract_values('/v1/delivery-estimates/GcfU8g0c_pxJXR8spP3uc4jMX')
    assert 'estimate' == path_item2.entity
    assert  'GcfU8g0c_pxJXR8spP3uc4jMX'== path_item2.id 
    
    path_item3 = analyzer.extract_values('/v1/borderless-accounts')
    assert 'account' == path_item3.entity
    assert  path_item3.id is None
    
    path_item4 = analyzer.extract_values('/v3/profiles/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/borderless-accounts/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/statement.json')
    assert 'statement' == path_item4.entity
    assert  'QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS'== path_item4.id# TODO
    
   
