from slugify import slugify
from application_profile import ApplicationProfile

"""
Loops over all terms in the application profile and generates slugs that
can serve as page filenames. The `transform` method can be used to transform
an IRI to a slug, falling back to the full IRI.
"""
class Sluggifier:

    slugs: dict[str, str]

    def __init__(self, application_profile: ApplicationProfile):
        self.slugs = dict()

        for term in application_profile.mappings.values():
            slug = self._find_slug(term['@id'], self.slugs.values())
            self.slugs[term['@id']] = slug

    def transform(self, iri: str) -> str:
        if iri in self.slugs:
            return f'{self.slugs[iri]}.html'
        else:
            return iri

    def _find_slug(self, not_a_slug: str, existing_slugs: list[str]) -> str:
        slug = slugify(not_a_slug)
        i = 0
        while slug in existing_slugs:
            i += 1
            slug = slugify(not_a_slug) + '-' + str(i)
        return slug
