import json
import os
import uuid
from pyld import jsonld

"""
Loads the application profile from a file and parses it into some
usefuls dictionaries.
"""
class ApplicationProfile():
    # Schemas, maps from term (or: alias) to schema IRI
    schemas = dict()

    # Mappings, from term to the term definition
    mappings = dict()

    id_to_term = dict()

    def __init__(self, path):
        if not (os.path.exists(path) and os.path.isfile(path)):
            raise Exception('Warning: application profile path does not lead to a file')

        with open(path) as contents:
            data = json.load(contents)

        context = data['@context']

        # Mapping objects from the pyld package help us parse the CURIEs and more
        self.mappings.update(self._get_mappings_from_context(data))
        self.id_to_term = { v['@id']: k for k, v in self.mappings.items() }

        # All terms that start with http:// or https:// are schemas
        # This needs to be done first so that all schemas are available when we loop over the terms
        self.schemas = {k: v for k, v in context.items() if type(context[k]) == str and (
            context[k].startswith('http://') or context[k].startswith('https://'))}

    def curie_to_full_iri(self, curie):
        return self.mappings[curie]['@id']

    def full_iri_to_curie(self, iri):
        return next(k for k, n in self.mappings.items() if n['@id'] == iri)

    def get_terms_per_schema(self):
        terms_per_schema = dict()

        for schema in self.schemas.keys():
            terms_per_schema[schema] = list()

        terms_per_schema['unknown'] = list()

        for term, definition in self.mappings.items():
            if term not in self.mappings:
                terms_per_schema['unknown'].append(term)
                continue

            schema_with_longest_overlap = ''
            for alias, iri in self.schemas.items():
                if self.mappings[term]['@id'].startswith(iri) and (schema_with_longest_overlap == '' or len(iri) > len(self.schemas[schema_with_longest_overlap])):
                    schema_with_longest_overlap = alias

            if schema_with_longest_overlap == '':
                terms_per_schema['unknown'].append(term)
                continue

            if schema_with_longest_overlap == term:
                continue

            terms_per_schema[schema_with_longest_overlap].append(term)

        if len(terms_per_schema['unknown']) == 0:
            del terms_per_schema['unknown']

        return terms_per_schema


    def _get_mappings_from_context(self, data):
        active_ctx = {'_uuid': str(
            uuid.uuid1()), 'processingMode': 'json-ld-1.1', 'mappings': {}}
        return jsonld.JsonLdProcessor().process_context(active_ctx, data, {})['mappings']
