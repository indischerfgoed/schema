import os
import shutil
from rdflib import URIRef, RDFS, RDF
import config
import markdown

from application_profile import ApplicationProfile
from schemas import Schemas
from sluggifier import Sluggifier
from utils import flatten, write_to_file


DOMAIN_INCLUDES = 'http://schema.org/domainIncludes'
RANGE_INCLUDES = 'http://schema.org/rangeIncludes'

""" Loads the application profile and schemas from disk and generates documentation pages. """
def main():
    # Load application profile
    application_profile = ApplicationProfile(
        config.input['application_profile'])
    # Load schemas
    schemas = Schemas(config.input['schemas'],
                      config.input['domain'], config.input['range'])
    # Create slugs for all application profile entries
    slugs = Sluggifier(application_profile)
    # Create the output directory
    if os.path.exists(config.output['folder']):
        shutil.rmtree(config.output['folder'])
    os.makedirs(config.output['folder'], exist_ok=True)
    # Generate the documentation pages
    generate_index_page(application_profile, slugs)
    generate_term_pages(application_profile, schemas, slugs)


def generate_index_page(application_profile: ApplicationProfile, slugs: Sluggifier):
    # Write title and description to the index page
    index_page_contents = f'# {config.meta["title"]}\n'
    index_page_contents += f'{config.meta["description"]}\n'

    # Loop over all terms per schema and list the terms in those schemas
    for s, terms in application_profile.get_terms_per_schema().items():
        # Write the schema name to the index page
        index_page_contents += f'\n\n## {s}\n'

        # Write the schema base IRI to the index page (unless the schema is 'unknown')
        if s in application_profile.schemas:
            index_page_contents += f'{config.language["THE_BASE_IRI_IS"]}: [{application_profile.schemas[s]}]({application_profile.schemas[s]})\n\n'

        # Write all terms in this schema to the index page
        for term in sorted(terms):
            full = application_profile.mappings[term]['@id']
            index_page_contents += f' - [{term}]({slugs.transform(full)})\n'

    markdown_to_file(index_page_contents, 'index.html')


def generate_term_pages(application_profile: ApplicationProfile, schemas: Schemas, slugs: Sluggifier):
    for terms in application_profile.get_terms_per_schema().values():
        # Generate the documentation page for this specific term
        for term in sorted(terms):
            full = application_profile.mappings[term]['@id']
            term_contents = term_to_markdown(
                term, full, slugs, application_profile, schemas)
            markdown_to_file(term_contents, slugs.transform(full))

""" Generates a Markdown page for a given term """
def term_to_markdown(term: str, uri: str, slugs: Sluggifier, application_profile: ApplicationProfile, schemas: Schemas):

    """ Returns a Markdown link to the given IRI """
    def get_reference(iri: str) -> str:
        name = application_profile.id_to_term[iri] if iri in application_profile.id_to_term else iri
        return f"[{name}]({slugs.transform(iri)})"

    classes = schemas.get_classes(uri)

    # HEADER

    contents = f'[< {config.language["GO_BACK"]}](../)\n'
    contents += f'# {term}\n\n'
    contents += f"##### {uri}\n"

    # BREADCRUMBS

    breadcrumbs = schemas.get_breadcrumbs(uri)
    for bc in breadcrumbs:
        contents += ' > '.join([get_reference(str(c)) for c in bc]) + '\n'
    contents += '\n'

    # DESCRIPTION

    for o in schemas.graph.objects(URIRef(uri), RDFS.comment):
        contents += '\n' + str(o) + '\n\n'

    # The item is a Class
    if RDFS.Class in classes:

        # PROPERTIES

        contents += f'### {config.language["PROPERTIES"]}\n\n'

        # All properties for this class that are also in the application profile
        properties = application_profile.filter(schemas.get_properties_with_class_as_domain(uri))

        if len(properties) > 0:
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for prop in properties:
                # Property (with link)
                contents += get_reference(str(prop)) + ' | '

                # Range (with links)
                range = application_profile.filter(schemas.get_range(prop, with_subclasses = True))
                contents += ', '.join(map(lambda r: get_reference(str(r)), range)) + ' | '

                # Description
                comments = schemas.get_comment(prop)
                contents += ' | '.join(comments).replace('\n', '')

                contents += '\n'

            contents += '\n'

        else:
            contents += f'{config.language["NO_DIRECT_PROPERTIES"]}\n\n'

        # INHERITED PROPERTIES

        super_classes = list(filter(lambda x: x != uri, list(
            dict.fromkeys(flatten(breadcrumbs)[::-1]))))

        for super_class in super_classes:
            indirect_properties = application_profile.filter(schemas.get_properties_with_class_as_domain(super_class))

            if len(indirect_properties) > 0:
                super_class_term = application_profile.id_to_term[super_class] if super_class in application_profile.id_to_term else super_class
                contents += f'*{config.language["SUBCLASSES_OF"]} {super_class_term} {config.language["MAY_HAVE_THE_FOLLOWING_PROPERTIES"]}:*\n\n'

                contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

                for prop in indirect_properties:
                    # Property (with link)
                    contents += get_reference(str(prop)) + ' | '

                    # Range (with links)
                    range = application_profile.filter(schemas.get_range(prop, with_subclasses = True))
                    contents += ', '.join(map(lambda r: get_reference(str(r)), range)) + ' | '

                    # Description
                    comments = schemas.get_comment(prop)
                    contents += ' | '.join(comments).replace('\n', '')

                    contents += '\n'

            contents += '\n'

        # RANGE

        range = application_profile.filter(schemas.get_properties_with_class_as_range(uri, with_subclasses = True))

        if len(range) > 0:

            contents += f'### {config.language["INSTANCES"]}\n\n'
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_APPEAR_AS_VALUE"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["ON_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for property in range:
                ref = get_reference(str(property))

                domain = application_profile.filter(schemas.get_domain(property, with_subclasses = True))
                domain_str = ', '.join(map(lambda d: get_reference(str(d)), domain))

                label = '. '.join(schemas.get_comment(property)) or ''
                contents += f"{ref} | {domain_str} | {label} \n"

            contents += '\n'

        # SUBCLASSES
        
        more_specific = application_profile.filter(schemas.get_subclasses(uri))

        if len(more_specific) > 0:
            contents += f'### {config.language["MORE_SPECIFIC_TYPES"]}\n\n'
            contents += f'*{config.language["THESE_CLASSES_ARE_SUBCLASSES_OF"]} {term}:*\n\n'

            contents += f'{config.language["CLASS"]} | {config.language["DESCRIPTION"]}\n--- | ---\n'
            for c in more_specific:
                ref = get_reference(str(c))
                label = '. '.join(schemas.get_comment(c)) or ''
                contents += f"{ref} | {label} \n"

            contents += '\n\n\n'

        contents += '\n\n\n'

    if RDF.Property in classes:
        domain = application_profile.filter(schemas.get_domain(uri, with_subclasses = True))

        if len(domain) > 0:
            contents += f'### {config.language["DOMAIN"]}\n'
            contents += f'{config.language["PROPERTY_USED_ON_THESE_TYPES"]}\n\n'
            for item in domain:
                contents += ' - ' + \
                    get_reference(str(item)) + '\n'
            contents += '\n\n\n'
        
        range = application_profile.filter(schemas.get_range(uri))

        if len(range) > 0:
            contents += f'### {config.language["RANGE"]}\n'
            contents += f'{config.language["VALUES_ARE_OF_THESE_TYPES"]}\n\n'
            for item in range:
                contents += ' - ' + \
                    get_reference(str(item)) + '\n'
            contents += '\n\n\n'

    return contents



""" Saves a Markdown string as an HTML file """
def markdown_to_file(content: str, filename: str):
    path = os.path.join(config.output['folder'], filename)
    html = markdown.markdown(content, extensions=['tables'])
    with open(config.input['html_template']) as template:
        write_to_file(path, template.read().replace('{CONTENT}', html).replace('{TITLE}', config.meta['title']))


if __name__ == "__main__":
    main()
