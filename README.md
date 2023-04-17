# Data model voor project indisch erfgoed digitaal

Voor het project indisch erfgoed digitaal gebruiken we een [applicatie profiel](./jsonldcontext.json) dat een aantal bestaande schema's hergebuikt, zoals [schema.org](http://schema.org), [prov-o](https://www.w3.org/TR/prov-o/) en [SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/). Extra types en relaties die nodig zijn voor het indisch ergoed hebben we gedefinieerd als [extensie van schema.org](./schema_ext-indischerfgoed.ttl). 

Hieronder beschrijven we het model in hoofdlijnen. We tonen alleen de types en relaties daartussen. Raadpleeg de volledige documentatie voor meer details, zoals alle attributen voor een type.

## Event
Centraal in het model staat het Event (paars). 
![Event model](./assets/event_model.jpg "Event model")

Het type event specifieren we in een aantal subtypes.
![Event types](./assets/event_types.jpg "Event types")

## CreativeWork
De collectie objecten beschouwen we als werken (CreativeWork). 
![Werk model](./assets/work_model.jpg "Werk model")

Het type werk specificeren we in een aantal subtypes.
![Werk types](./assets/work_types.jpg "Werk types")

## Person
![Person model](./assets/person_model.jpg "Person model")

