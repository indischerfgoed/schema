import os
import shutil
from rdflib import URIRef, RDFS, RDF
import json
import config
import markdown

from application_profile import ApplicationProfile
from schemas import Schemas
from sluggifier import Sluggifier
from utils import flatten, write_to_file


# https://stackoverflow.com/questions/61726754/are-schemadomainincludes-and-rdfsdomain-as-well-as-schemarangeincludes-and-r
DOMAIN_INCLUDES = 'http://schema.org/domainIncludes'
RANGE_INCLUDES = 'http://schema.org/rangeIncludes'


def main():
    # Load application profile
    application_profile = ApplicationProfile(
        config.input['application_profile'])
    # Load schemas
    schemas = Schemas(config.input['schemas'])
    # Create slugs for all application profile entries
    slugs = Sluggifier(application_profile)
    # Now generate the documentation pages
    generate_pages(application_profile, schemas, slugs)


def generate_pages(ap, schemas, slugs: Sluggifier):
    # Create the output directory
    if os.path.exists(config.output['folder']):
        shutil.rmtree(config.output['folder'])
    os.makedirs(config.output['folder'], exist_ok=True)

    # Build the index page
    index_page_contents = f'# {config.meta["title"]}\n{config.meta["description"]}\n'

    # now generate the term pages (id_to_slug is complete now)
    for s, terms in ap.get_terms_per_schema().items():
        index_page_contents += f'\n\n## {s}\n'
        if s in ap.schemas:
            index_page_contents += f'{config.language["THE_BASE_IRI_IS"]}: [{ap.schemas[s]}]({ap.schemas[s]})\n\n'

        for term in sorted(terms):
            full = ap.mappings[term]['@id']
            index_page_contents += f' - [{term}]({slugs.transform(full)})\n'

        for term in sorted(terms):
            if term in ap.mappings:
                full = ap.mappings[term]['@id']
                term_contents = term_to_markdown(
                    term, full, slugs, ap, schemas)
                markdown_to_file(term_contents, slugs.transform(full))

    markdown_to_file(index_page_contents, 'index.html')


def term_to_markdown(term: str, uri: str, slugs: Sluggifier, application_profile: ApplicationProfile, schemas: Schemas):

    classes = schemas.get_classes(uri)

    # HEADER

    contents = f'[< {config.language["GO_BACK"]}](../)\n'
    contents += f'# {term}\n\n'
    contents += f"##### {uri}\n"

    # BREADCRUMBS

    breadcrumbs = schemas.get_breadcrumbs(uri)
    for bc in breadcrumbs:
        contents += ' > '.join([get_reference(str(c), slugs,
                               application_profile.id_to_term) for c in bc]) + '\n'
    contents += '\n'

    # DESCRIPTION

    for o in schemas.graph.objects(URIRef(uri), RDFS.comment):
        contents += '\n' + str(o) + '\n\n'

    if RDFS.Class in classes:

        # PROPERTIES

        contents += f'### {config.language["PROPERTIES"]}\n\n'

        direct_properties_in_schemas = [s for s in schemas.graph.subjects(RDFS.domain, URIRef(
            uri))] + [s for s in schemas.graph.subjects(URIRef(DOMAIN_INCLUDES), URIRef(uri))]
        direct_properties = [p for p in direct_properties_in_schemas if str(
            p) in application_profile.id_to_term]

        if len(direct_properties) > 0:
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for prop in direct_properties:
                # Property (with link)
                contents += get_reference(str(prop), slugs,
                                          application_profile.id_to_term) + ' | '

                # Range (with links)
                range = [o for o in schemas.graph.objects(
                    prop, RDFS.range)] + [o for o in schemas.graph.objects(prop, URIRef(RANGE_INCLUDES))]
                contents += ', '.join(map(lambda r: get_reference(str(r),
                                      slugs, application_profile.id_to_term), range)) + ' | '

                # Description
                comments = [o for o in schemas.graph.objects(
                    prop, RDFS.comment)]
                contents += ' | '.join(comments).replace('\n', '')

                contents += '\n'

            contents += '\n'

        else:
            contents += f'{config.language["NO_DIRECT_PROPERTIES"]}\n'

        super_classes = list(filter(lambda x: x != uri, list(
            dict.fromkeys(flatten(breadcrumbs)[::-1]))))

        for super_class in super_classes:
            indirect_properties_in_schemas = [s for s in schemas.graph.subjects(RDFS.domain, URIRef(
                super_class))] + [s for s in schemas.graph.subjects(URIRef(DOMAIN_INCLUDES), URIRef(super_class))]
            indirect_properties = [p for p in indirect_properties_in_schemas if str(
                p) in application_profile.id_to_term]

            if len(indirect_properties) > 0:
                contents += f'*{config.language["SUBCLASSES_OF"]} {super_class} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

                contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

                for prop in indirect_properties:
                    # Property (with link)
                    contents += get_reference(str(prop), slugs,
                                              application_profile.id_to_term) + ' | '

                    # Range (with links)
                    range = [o for o in schemas.graph.objects(
                        prop, RDFS.range)] + [o for o in schemas.graph.objects(prop, URIRef(RANGE_INCLUDES))]
                    contents += ', '.join(map(lambda r: get_reference(
                        str(r), slugs, application_profile.id_to_term), range)) + ' | '

                    # Description
                    comments = [o for o in schemas.graph.objects(
                        prop, RDFS.comment)]
                    contents += ' | '.join(comments).replace('\n', '')

                    contents += '\n'

            contents += '\n'

        # RANGE

        range_in_schemas = [s for s in schemas.graph.subjects(RDFS.range, URIRef(
            uri))] + [s for s in schemas.graph.subjects(URIRef(RANGE_INCLUDES), URIRef(uri))]
        range = [p for p in range_in_schemas if str(
            p) in application_profile.id_to_term]

        if len(range) > 0:

            contents += f'### {config.language["INSTANCES"]}\n\n'
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_APPEAR_AS_VALUE"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["ON_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for property in range:
                ref = get_reference(str(property), slugs,
                                    application_profile.id_to_term)
                domain_in_schemas = [o for o in schemas.graph.objects(
                    property, RDFS.domain)] + [o for o in schemas.graph.objects(property, URIRef(DOMAIN_INCLUDES))]
                domain = [p for p in domain_in_schemas if str(
                    p) in application_profile.id_to_term]
                domain_str = ', '.join(map(lambda d: get_reference(
                    str(d), slugs, application_profile.id_to_term), domain))

                label = '. '.join(schemas.graph.objects(
                    property, RDFS.comment)) or ''
                contents += f"{ref} | {domain_str} | {label} \n"

            contents += '\n'

        # SUBCLASSES

        more_specific_in_schemas = [
            s for s in schemas.graph.subjects(RDFS.subClassOf, URIRef(uri))]
        more_specific = [p for p in more_specific_in_schemas if str(
            p) in application_profile.id_to_term]

        if len(more_specific) > 0:
            contents += f'### {config.language["MORE_SPECIFIC_TYPES"]}\n\n'
            contents += f'*{config.language["THESE_CLASSES_ARE_SUBCLASSES_OF"]} {term}:*\n\n'

            contents += f'{config.language["CLASS"]} | {config.language["DESCRIPTION"]}\n--- | ---\n'
            for c in more_specific:
                ref = get_reference(
                    str(c), slugs, application_profile.id_to_term)
                label = '. '.join(schemas.graph.objects(c, RDFS.comment)) or ''
                contents += f"{ref} | {label} \n"

            contents += '\n\n\n'

        contents += '\n\n\n'

    if RDF.Property in classes:
        domain_in_schemas = [o for o in schemas.graph.objects(URIRef(
            uri), RDFS.domain)] + [o for o in schemas.graph.objects(URIRef(uri), URIRef(DOMAIN_INCLUDES))]
        domain = [p for p in domain_in_schemas if str(
            p) in application_profile.id_to_term]

        if len(domain) > 0:
            contents += f'### {config.language["DOMAIN"]}\n'
            contents += f'{config.language["PROPERTY_USED_ON_THESE_TYPES"]}\n\n'
            for item in domain:
                contents += ' - ' + \
                    get_reference(str(item), slugs,
                                  application_profile.id_to_term) + '\n'
            contents += '\n\n\n'

        range_in_schemas = [o for o in schemas.graph.objects(URIRef(
            uri), RDFS.range)] + [o for o in schemas.graph.objects(URIRef(uri), URIRef(RANGE_INCLUDES))]
        range = [p for p in domain_in_schemas if str(
            p) in application_profile.id_to_term]

        if len(range) > 0:
            contents += f'### {config.language["RANGE"]}\n'
            contents += f'{config.language["VALUES_ARE_OF_THESE_TYPES"]}\n\n'
            for item in range:
                contents += ' - ' + \
                    get_reference(str(item), slugs,
                                  application_profile.id_to_term) + '\n'
            contents += '\n\n\n'

    return contents


def get_reference(id: str, slugs: Sluggifier, node_id_to_human_readable):
    name = node_id_to_human_readable[id] if id in node_id_to_human_readable else id
    return f"[{name}]({slugs.transform(id)})"



def markdown_to_file(content: str, filename: str):
    path = os.path.join(config.output['folder'], filename)
    html = markdown.markdown(content, extensions=['tables'])
    with open(config.input['html_template']) as template:
        write_to_file(path, template.read().replace('{CONTENT}', html))



if __name__ == "__main__":
    main()
