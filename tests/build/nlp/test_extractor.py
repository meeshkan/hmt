from meeshkan.build.nlp.entity_extractor import EntityExtractor


'''def test_github():
    extractor = EntityExtractor()
    #extractor.train(['/search/users', ])
    assert 'user' == extractor.get_entity_from_url('/search/users')


def test_opbank():
    extractor = EntityExtractor()
    # extractor.train(['/accounts/v3/accounts',
    #                  '/accounts/v3/accounts/GcfU8g0c_pxJXR8spP3uc4jMXRwalQyIDwj820w8-TY.8vlH6Nvrzd0fFiaSD6U4_Q.hR3Bjufb_ZzypZXU707zJg',
    #                  '/v1/payments/initiate',
    #                  '/v1/payments/confirm'])

    assert 'payment' == extractor.get_entity_from_url('/v1/payments/confirm')
    assert 'account' == extractor.get_entity_from_url('/accounts/v3/accounts/GcfU8g0c_pxJXR8spP3uc4jMXRwalQyIDwj820w8-TY.8vlH6Nvrzd0fFiaSD6U4_Q.hR3Bjufb_ZzypZXU707zJg')
'''

def test_transferwise():
    extractor = EntityExtractor()
    # extractor.train(['/v3/profiles/saf45gdrg4gsdf/transfers/sdfsr456ygh56ujhgf/payments',
    #                  '/v1/delivery-estimates/GcfU8g0c_pxJXR8spP3uc4jMX',
    #                  '/v1/borderless-accounts',
    #                  '/v3/profiles/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/borderless-accounts/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/statement.json'])

    assert 'payment' == extractor.get_entity_from_url('/v3/profiles/saf45gdrg4gsdf/transfers/sdfsr456ygh56ujhgf/payments')
    assert 'estimate' == extractor.get_entity_from_url('/v1/delivery-estimates/GcfU8g0c_pxJXR8spP3uc4jMX')
    assert 'account' == extractor.get_entity_from_url('/v1/borderless-accounts')
    assert 'statement' == extractor.get_entity_from_url('/v3/profiles/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/borderless-accounts/QyIDwj820w8-TY.8vlH6Nvrzd0fFiaS/statement.json')








