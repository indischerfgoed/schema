import os
from rdflib import Graph, URIRef, RDFS, RDF, OWL
from utils import flatten


class Schemas():

    def __init__(self, paths, domain: list[str] = [str(RDFS.domain)], range: list[str] = [str(RDFS.range)]):
        # Load schemas from config into a graph
        self.graph = Graph()
        queue = paths.copy()
        for s in queue:
            if os.path.isdir(s):
                for f in os.listdir(s):
                    self.graph.parse(os.path.join(s, f))
            elif os.path.isfile(s):
                self.graph.parse(s)
            else:
                raise Exception(f'Warning: {s} is not a file or directory')

        # Maps IRIs of objects to a list of all their predecessors.
        # Used to build the breadcrumbs
        self.predecessors = {
            str(s): [str(o) for o in self.graph.objects(s, RDFS.subClassOf)] for s in self.graph.subjects(RDFS.subClassOf, None)
        }

        self.domain = domain
        self.range = range

    """ Get all classes for a given URI """
    def get_classes(self, iri: str) -> list[str]:
        return [o for o in self.graph.objects(URIRef(iri), RDF.type)]
    
    def get_all_classes(self) -> list[str]:
        return list(set([str(s) for s in self.graph.subjects(RDF.type, RDFS.Class)] + [str(s) for s in self.graph.subjects(RDF.type, OWL.Class)]))
    
    def get_properties_with_class_as_domain(self, class_iri: str) -> list[str]:
        result = []
        for domain in self.domain:
            result += [s for s in self.graph.subjects(URIRef(domain), URIRef(class_iri))]
        return result
    
    def get_properties_with_class_as_range(self, class_iri: str, with_subclasses = False) -> list[str]:
        result = []
        for range in self.range:
            result += [s for s in self.graph.subjects(URIRef(range), URIRef(class_iri))]
        if with_subclasses:
            return self._with_subclasses(result)
        else:
            return result

    def get_range(self, iri: str, with_subclasses = False) -> list[str]:
        result = []
        for range in self.range:
            result += [o for o in self.graph.objects(URIRef(iri), URIRef(range))]
        if with_subclasses:
            return self._with_subclasses(result)
        else:
            return result

    def get_domain(self, iri: str, with_subclasses = False) -> list[str]:
        result = []
        for domain in self.domain:
            result += [o for o in self.graph.objects(URIRef(iri), URIRef(domain))]
        if with_subclasses:
            return self._with_subclasses(result)
        else:
            return result
    
    def get_subclasses(self, iri: str) -> list[str]:
        return [s for s in self.graph.subjects(RDFS.subClassOf, URIRef(iri))]
    
    def get_superclasses(self, iri: str) -> list[str]:
        if iri == 'http://schema.org/Photograph':
            print(iri)
        return [o for o in self.graph.objects(URIRef(iri), RDFS.subClassOf)]
    
    def get_comment(self, iri: str) -> list[str]:
        return [o for o in self.graph.objects(URIRef(iri), RDFS.comment)]
    
    def get_label(self, iri: str) -> list[str]:
        return [o for o in self.graph.objects(URIRef(iri), RDFS.label)]

    def get_breadcrumbs(self, id: str):
        if id not in self.predecessors:
            return [[id]]
        ps = [p for p in self.predecessors[id] if p is not id]
        if len(ps) == 0:
            return [[id]]

        breadcrumbs = []
        for parent in self.predecessors[id]:
            for bc in self.get_breadcrumbs(parent):
                bc.extend([id])
                breadcrumbs.append(bc)
        return breadcrumbs
    
    def _with_subclasses(self, iris: list[str]) -> list[str]:
        return flatten([[iri] + self.get_subclasses(iri) for iri in iris])

