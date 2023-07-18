import os
import shutil
from rdflib import URIRef, RDFS, RDF
import config
import markdown

from application_profile import ApplicationProfile
from schemas import Schemas
from sluggifier import Sluggifier
from utils import flatten, write_to_file


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
    generate_index_pages(application_profile, schemas, slugs)
    generate_term_pages(application_profile, schemas, slugs)


def generate_index_pages(application_profile: ApplicationProfile, schemas: Schemas, slugs: Sluggifier):
    # Write title and description to the index page
    index_page_contents = f'{config.meta["description"]}\n\n'

    # Get all classes in the schemas
    classes = schemas.get_all_classes()

    # Keep only those in AP
    classes_in_profile = application_profile.filter(classes)

    # Find the classes without a superclass in the AP (roots)
    roots = list(filter(lambda c: len(application_profile.filter(schemas.get_superclasses(c))) == 0, classes_in_profile))


    def _build_tree_component(iri: str, indent = ''):
        term = application_profile.id_to_term[iri]
        res = f'{indent}- [{term}]({slugs.transform(iri)})\n'
        sub_classes = application_profile.filter(schemas.get_subclasses(iri))
        for sub_class in sub_classes:
            res += _build_tree_component(sub_class, indent + '    ')
        return res

    index_page_contents += f'#### {config.language["CLASS_TREE"]}:\n\n'

    # For each of these, list their subclasses
    for root in sorted(roots, key = lambda r: application_profile.id_to_term[r]):
        term = application_profile.id_to_term[root]
        index_page_contents += _build_tree_component(root)



    markdown_to_file(index_page_contents, 'index.html')


    schemas_index_page_contents = ''
    # Loop over all terms per schema and list the terms in those schemas
    for s, terms in application_profile.get_terms_per_schema().items():
        # Write the schema name to the index page
        schemas_index_page_contents += f'\n\n## {s}\n'

        # Write the schema base IRI to the index page (unless the schema is 'unknown')
        if s in application_profile.schemas:
            schemas_index_page_contents += f'{config.language["THE_BASE_IRI_IS"]}: [{application_profile.schemas[s]}]({application_profile.schemas[s]})\n\n'

        # Write all terms in this schema to the index page
        for term in sorted(terms):
            full = application_profile.mappings[term]['@id']
            schemas_index_page_contents += f' - [{term}]({slugs.transform(full)})\n'

    markdown_to_file(schemas_index_page_contents, 'schemas.html')


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
        if iri in application_profile.id_to_term:
            name = application_profile.id_to_term[iri]
        else:
            labels = schemas.get_label(iri)
            name = labels[0] if len(labels) > 0 else iri
            name += ' &#x2197;'

        return f"[{name}]({slugs.transform(iri)})"

    classes = schemas.get_classes(uri)

    contents = ''

    # BREADCRUMBS

    breadcrumbs = schemas.get_breadcrumbs(uri)
    for bc in breadcrumbs:
        contents += ' > '.join([get_reference(str(c)) for c in bc]) + '\n'
    contents += '\n'

    # HEADER

    contents += f'# {term}\n\n'
    contents += f"{uri}\n\n"

    # DESCRIPTION

    for o in schemas.graph.objects(URIRef(uri), RDFS.comment):
        contents += '\n' + str(o) + '\n\n'

    # The item is a Class
    if RDFS.Class in classes:

        # PROPERTIES

        contents += f'### {config.language["PROPERTIES_FROM"]} {term}\n\n'

        # All properties for this class that are also in the application profile
        properties = application_profile.filter(schemas.get_properties_with_class_as_domain(uri))

        if len(properties) > 0:
            contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for prop in properties:
                # Property (with link)
                contents += get_reference(str(prop)) + ' | '

                # Range (with links)
                range = schemas.get_range(prop, with_subclasses = False)
                range_in_profile = application_profile.filter(range)
                range_out_of_profile = list(filter(lambda iri: str(iri) not in range_in_profile, range))
                contents += ', '.join(map(lambda r: get_reference(str(r)), range_in_profile))
                contents += ', ' if len(range_in_profile) > 0 and len(range_out_of_profile) > 0 else ''
                contents += ', '.join(map(lambda r: get_reference(str(r)), range_out_of_profile))
                contents += ' | '

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

                contents += f'### {config.language["PROPERTIES_FROM"]} {super_class_term}\n\n'


                contents += f'{config.language["PROPERTY"]} | {config.language["EXPECTED_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

                for prop in indirect_properties:
                    # Property (with link)
                    contents += get_reference(str(prop)) + ' | '

                    # Range (with links)
                    range = schemas.get_range(prop, with_subclasses = False)
                    range_in_profile = application_profile.filter(range)
                    range_out_of_profile = list(filter(lambda iri: str(iri) not in range_in_profile, range))
                    contents += ', '.join(map(lambda r: get_reference(str(r)), range_in_profile))
                    contents += ', ' if len(range_in_profile) > 0 and len(range_out_of_profile) > 0 else ''
                    contents += ', '.join(map(lambda r: get_reference(str(r)), range_out_of_profile))
                    contents += ' | '

                    # Description
                    comments = schemas.get_comment(prop)
                    contents += ' | '.join(comments).replace('\n', '')

                    contents += '\n'

            contents += '\n'

        # RANGE

        range = application_profile.filter(schemas.get_properties_with_class_as_range(uri, with_subclasses = False))

        if len(range) > 0:

            contents += f'### {config.language["INSTANCES"]}\n\n'
            contents += f'*{config.language["INSTANCES_OF"]} {term} {config.language["MAY_APPEAR_AS_VALUE"]}:*\n\n'

            contents += f'{config.language["PROPERTY"]} | {config.language["ON_TYPE"]} | {config.language["DESCRIPTION"]}\n--- | --- | ---\n'

            for property in range:
                ref = get_reference(str(property))

                domain = application_profile.filter(schemas.get_domain(property, with_subclasses = False))
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
        domain = application_profile.filter(schemas.get_domain(uri, with_subclasses = False))

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
