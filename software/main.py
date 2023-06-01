import os
import shutil
import json
from rdflib import Graph, URIRef, RDFS, RDF
import json
from application_profile import ApplicationProfile
import config
from slugify import slugify

# https://stackoverflow.com/questions/61726754/are-schemadomainincludes-and-rdfsdomain-as-well-as-schemarangeincludes-and-r
DOMAIN_INCLUDES = 'http://schema.org/domainIncludes'
RANGE_INCLUDES = 'http://schema.org/rangeIncludes'

def main():
    # Check if the application profile exists
    if not (os.path.exists(config.input['application_profile']) and os.path.isfile(config.input['application_profile'])):
        raise Exception('Warning: application profile path does not lead to a file')

    # Load schemas from config into a graph
    schemas = Graph()
    queue = config.input['schemas'].copy()
    for s in queue:
        if os.path.isdir(s):
            for f in os.listdir(s):
                schemas.parse(os.path.join(s, f))
        elif os.path.isfile(s):
            schemas.parse(s)
        else:
            raise Exception(f'Warning: {s} is not a file or directory')

    # Create the output directory
    if os.path.exists(config.output['folder']):
        shutil.rmtree(config.output['folder'])
    os.makedirs(config.output['folder'], exist_ok=True)

    # Open application profile and parse JSON-LD contents
    ap = None
    if os.path.exists(config.input['application_profile']) and os.path.isfile(config.input['application_profile']):
        with open(config.input['application_profile']) as contents:
            parsed_ap_contents = json.load(contents)
            ap = ApplicationProfile(parsed_ap_contents)

    if ap is None:
        raise Exception('Warning: application profile could not be parsed')

    id_to_slug = dict()

    # Create the application profile as an index page for the schema
    # Use application profile file as index page

    contents = f'# {config.meta["title"]}\n' + \
            f'{config.meta["description"]}\n'

    predecessors = { str(s): [str(o) for _, _, o in schemas.triples((s, RDFS.subClassOf, None))] for s, _, _ in schemas.triples((None, RDFS.subClassOf, None)) }

    # Get the terms in the application profile per schema
    for s, terms in ap.get_terms_per_schema().items():
        contents += f'\n\n##### {s}\n'
        if s in ap.schemas:
            contents += f'{config.language["THE_BASE_IRI_IS"]}: [{ap.schemas[s]}]({ap.schemas[s]})\n\n'

        for term in sorted(terms):
            full = ap.mappings[term]['@id']

            uri = URIRef(full)
            if (uri, None, None) in schemas:
                readable = term # TODO: get the label from graph perhaps?
                slug = find_slug(full, id_to_slug.values())
                id_to_slug[full] = slug
                contents += f' - [{readable}]({slug}.md)\n'

                term_contents = term_to_markdown(term, full, predecessors, id_to_slug, ap.id_to_term, schemas)
                write_to_file(os.path.join(config.output['folder'], slug + '.md'), term_contents)

            else:
                contents += f' - [{term}]({full})\n'

    write_to_file(os.path.join(config.output['folder'], 'README.md'), contents)


def find_slug(not_a_slug: str, existing_slugs: list[str]) -> str:
    slug = slugify(not_a_slug)
    i = 0
    while slug in existing_slugs:
        i += 1
        slug = slugify(not_a_slug) + '-' + str(i)
    return slug


def write_to_file(filepath, contents):
    with open(filepath, 'w') as f:
        f.seek(0)
        f.write(contents)
        f.truncate()

def term_to_markdown(term, uri, predecessors, id_to_slug, id_to_term, schemas):

    types = [o for _, _, o in schemas.triples((URIRef(uri), RDF.type, None))]

    # HEADER

    contents = f'[< {config.language["GO_BACK"]}](../)\n'
    contents += f'# {term}\n\n'
    contents += f"###### {uri}\n"

    # BREADCRUMBS

    breadcrumbs = get_breadcrumbs(uri, predecessors)
    for bc in breadcrumbs:
        contents += ' > '.join([get_reference(c, id_to_slug, id_to_term, True) for c in bc]) + '\n'
    contents += '\n'

    # DESCRIPTION

    for _, _, o in schemas.triples((URIRef(uri), RDFS.comment, None)):
        contents += '\n' + str(o) + '\n\n'

    if RDFS.Class in types:

        # PROPERTIES

        contents += f'#### {config.language["PROPERTIES"]}\n\n'

        direct_properties_in_schemas = [s for s in schemas.subjects(RDFS.domain, URIRef(uri))] + [s for s in schemas.subjects(URIRef(DOMAIN_INCLUDES), URIRef(uri))]
        direct_properties = [p for p in direct_properties_in_schemas if str(p) in id_to_term]

        if len(direct_properties) > 0:
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for prop in direct_properties:
                # Property (with link)
                contents += get_reference(str(prop), id_to_slug, id_to_term, True) + ' | '

                # Range (with links)
                range = [o for o in schemas.objects(prop, RDFS.range)] + [o for o in schemas.objects(prop, URIRef(RANGE_INCLUDES))]
                contents += ', '.join(map(lambda r: get_reference(str(r), id_to_slug, id_to_term, True), range)) + ' | '

                # Description
                comments = [o for o in schemas.objects(prop, RDFS.comment)]
                contents += ' | '.join(comments).replace('\n', '')

                contents += '\n'

            contents += '\n'

        else:
            contents += f'{config.language["NO_DIRECT_PROPERTIES"]}\n'

        super_classes = list(filter(lambda x: x != uri, list(dict.fromkeys(flatten(breadcrumbs)[::-1]))))

        for super_class in super_classes:
            indirect_properties_in_schemas = [s for s in schemas.subjects(RDFS.domain, URIRef(super_class))] + [s for s in schemas.subjects(URIRef(DOMAIN_INCLUDES), URIRef(super_class))]
            indirect_properties = [p for p in indirect_properties_in_schemas if str(p) in id_to_term]

            if len(indirect_properties) > 0:
                contents += f'*{config.language["SUBCLASSES_OF"]} {super_class} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

                contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

                for prop in indirect_properties:
                    # Property (with link)
                    contents += get_reference(str(prop), id_to_slug, id_to_term, True) + ' | '

                    # Range (with links)
                    range = [o for o in schemas.objects(prop, RDFS.range)] + [o for o in schemas.objects(prop, URIRef(RANGE_INCLUDES))]
                    contents += ', '.join(map(lambda r: get_reference(str(r), id_to_slug, id_to_term, True), range)) + ' | '

                    # Description
                    comments = [o for o in schemas.objects(prop, RDFS.comment)]
                    contents += ' | '.join(comments).replace('\n', '')

                    contents += '\n'

            contents += '\n'


        # RANGE

        range_in_schemas = [s for s in schemas.subjects(RDFS.range, URIRef(uri))] + [s for s in schemas.subjects(URIRef(RANGE_INCLUDES), URIRef(uri))]
        range = [p for p in range_in_schemas if str(p) in id_to_term]

        if len(range) > 0:

            contents += f'#### {config.language["INSTANCES"]}\n\n'
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_APPEAR_AS_VALUE"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["ON_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for property in range:
                ref = get_reference(str(property), id_to_slug, id_to_term, True)
                domain_in_schemas = [o for o in schemas.objects(property, RDFS.domain)] + [o for o in schemas.objects(property, URIRef(DOMAIN_INCLUDES))]
                domain = [p for p in domain_in_schemas if str(p) in id_to_term]
                domain_str = ', '.join(map(lambda d: get_reference(d, id_to_slug, id_to_term, True), domain))

                label = '. '.join(schemas.objects(property, RDFS.comment)) or ''
                contents += f"{ref} | {domain_str} | {label} \n"

            contents += '\n'

        # SUBCLASSES

        more_specific_in_schemas = [s for s in schemas.subjects(RDFS.subClassOf, URIRef(uri))]
        more_specific = [p for p in more_specific_in_schemas if str(p) in id_to_term]

        if len(more_specific) > 0:
            contents += f'#### {config.language["MORE_SPECIFIC_TYPES"]}\n\n'
            contents += f'*{config.language["THESE_CLASSES_ARE_SUBCLASSES_OF"]} {term}:*\n\n'

            contents += f'{config.language["CLASS"]} | {config.language["DESCRIPTION"]}\n--- | ---\n'
            for c in more_specific:
                ref = get_reference(str(c), id_to_slug, id_to_term, True)
                label = '. '.join(schemas.objects(c, RDFS.comment)) or ''
                contents += f"{ref} | {label} \n"

            contents += '\n\n\n'

        contents += '\n\n\n'

    if RDF.Property in types:
        domain_in_schemas = [o for o in schemas.objects(URIRef(uri), RDFS.domain)] + [o for o in schemas.objects(URIRef(uri), URIRef(DOMAIN_INCLUDES))]
        domain = [p for p in domain_in_schemas if str(p) in id_to_term]

        if len(domain) > 0:
            contents += f'#### {config.language["DOMAIN"]}\n'
            contents += f'{config.language["PROPERTY_USED_ON_THESE_TYPES"]}\n\n'
            for item in domain:
                contents += ' - ' + \
                    get_reference(str(item), id_to_slug, id_to_term, True) + '\n'
            contents += '\n\n\n'

        range_in_schemas = [o for o in schemas.objects(URIRef(uri), RDFS.range)] + [o for o in schemas.objects(URIRef(uri), URIRef(RANGE_INCLUDES))]
        range = [p for p in domain_in_schemas if str(p) in id_to_term]

        if len(range) > 0:
            contents += f'#### {config.language["RANGE"]}\n'
            contents += f'{config.language["VALUES_ARE_OF_THESE_TYPES"]}\n\n'
            for item in range:
                contents += ' - ' + \
                    get_reference(str(item), id_to_slug, id_to_term, True) + '\n'
            contents += '\n\n\n'

    return contents


def get_breadcrumbs(id, predecessors):
    if id not in predecessors:
        return [[id]]
    ps = [p for p in predecessors[id] if p is not id]
    if len(ps) == 0:
        return [[id]]

    breadcrumbs = []
    for parent in predecessors[id]:
        for bc in get_breadcrumbs(parent, predecessors):
            bc.extend([id])
            breadcrumbs.append(bc)
    return breadcrumbs

def get_reference(id, node_id_to_slug, node_id_to_human_readable, nested=False):
    name = node_id_to_human_readable[id] if id in node_id_to_human_readable else id
    if id in node_id_to_slug:
        if nested:
            return f"[{name}]({os.path.join('./../', node_id_to_slug[id])})"
        else:
            return f"[{name}]({node_id_to_slug[id]}.md)"
    else:
        return f"[{name}]({id})"


def flatten(t: list[list[any]]) -> list[any]:
    return [item for sublist in t for item in sublist]


if __name__ == "__main__":
    main()
