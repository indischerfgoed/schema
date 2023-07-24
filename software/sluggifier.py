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
        self.application_profile = application_profile

    def transform(self, iri: str) -> str:
        if iri in self.application_profile.id_to_term:
            return f'{self.application_profile.id_to_term[iri]}.html'
        else:
            return iri
