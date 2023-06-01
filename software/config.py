input = dict(
  schemas=list(['./schemas', './schema_ext-indischerfgoed.ttl']),
  application_profile='./jsonldcontext.jsonld'
)

output = dict(
    folder='./doc'
)

meta = dict(
    title='PIED Model',
    description='...',
)

language = dict(
    CLASSES='Classes',
    CLASS='Class',
    PROPERTIES='Properties',
    INSTANCES='Instanties',
    GO_BACK='Ga terug',
    INSTANCES_OF='Instanties van',
    MAY_HAVE_THE_FOLLOWING_PROPERTIES='kunnen de volgende properties hebben',
    SUBCLASSES_OF='Sub-classes van',
    MAY_APPEAR_AS_VALUE='kunnen als waarde voor de volgende properties voorkomen',
    PROPERTY='Property',
    ON_TYPE='Op type',
    DESCRIPTION='Beschrijving',
    MORE_SPECIFIC_TYPES='Specifiekere types',
    THESE_CLASSES_ARE_SUBCLASSES_OF='Deze classes zijn sub-classes vas',
    DOMAIN='Domain',
    PROPERTY_USED_ON_THESE_TYPES='Deze property komt voor op de volgende types',
    DOMAIN_INCLUDES='Domain includes',
    RANGE='Range',
    VALUES_ARE_OF_THESE_TYPES='Waardes zijn van deze types',
    RANGE_INCLUDES='Range includes',
    EXPECTED_TYPE='Verwacht type',
    THE_BASE_IRI_IS='De IRI van dit schema is',
    NO_DIRECT_PROPERTIES='Deze class heeft geen directe properties',
)
