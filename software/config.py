from rdflib import RDFS

input = dict(
    schemas=list(['./schemas', './schema_ext-indischerfgoed.ttl']),
    application_profile='./jsonldcontext.jsonld',
    html_template='./software/template.html',
    # https://stackoverflow.com/questions/61726754/are-schemadomainincludes-and-rdfsdomain-as-well-as-schemarangeincludes-and-r
    domain=[str(RDFS.domain), 'http://schema.org/domainIncludes'],
    range=[str(RDFS.range), 'http://schema.org/rangeIncludes'],
)

output = dict(
    folder='./doc'
)

meta = dict(
    title='Application profile for Indisch Erfgoed',
    description='This is automatically generated documentation of the application profile for the Project Indisch Erfgoed Digitaal.',
)

language = dict(
    CLASSES='Types',
    CLASS='Type',
    CLASS_TREE='Type tree',
    PROPERTIES_FROM='Properties from',
    INSTANCES='Instances',
    GO_BACK='Go back',
    INSTANCES_OF='Instances of',
    MAY_APPEAR_AS_VALUE='may appear as a value for the following properties',
    PROPERTY='Property',
    ON_TYPE='On Type',
    DESCRIPTION='Description',
    MORE_SPECIFIC_TYPES='More specific types',
    THESE_CLASSES_ARE_SUBCLASSES_OF='These types are sub-classes of',
    DOMAIN='Domain',
    PROPERTY_USED_ON_THESE_TYPES='This property is used on these types',
    DOMAIN_INCLUDES='Domain includes',
    PROPERTY_MAY_BE_USED_ON_THESE_TYPES='This property may be used on these types',
    RANGE='Range',
    VALUES_ARE_OF_THESE_TYPES='Values are expected to be of these types',
    RANGE_INCLUDES='Range includes',
    VALUES_MAY_BE_OF_THESE_TYPES='Values may be of these types',
    EXPECTED_TYPE='Expected Type',
    THE_BASE_IRI_IS='The IRI of this schema is',
    NO_DIRECT_PROPERTIES='This type does not have direct properties.',
)
