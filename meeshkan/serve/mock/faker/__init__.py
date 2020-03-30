from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker

try:
    import spacy
    from meeshkan.serve.mock.faker.data_faker import MeeshkanDataFaker

    MeeshkanFaker = MeeshkanDataFaker
except ImportError:
    MeeshkanFaker = MeeshkanSchemaFaker
