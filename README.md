# Applicatie profiel voor het Project Indisch Erfgoed Digitaal

Het Project Indisch Erfgoed Eigitaal hergebruikt een aantal bestaande schema's zoals [schema.org](http://schema.org), [prov-o](https://www.w3.org/TR/prov-o/) en [SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/). De extra types en relaties die nodig zijn voor het indisch ergoed hebben we gedefinieerd als [extensie van schema.org](./schema_ext-indischerfgoed.ttl). 

De volledige set van types en properties zijn vastgelegd in een [jsonld context file](./jsonldcontext.jsonld). Raadpleeg de [documentatie](https://indischerfgoed.github.io/schema/) voor een leesbare weergave.

Hieronder beschrijven we het model in hoofdlijnen. 

## Event
Centraal in het model staat het Event (paars). 
![Event model](./assets/event_model.jpg "Event model")

## CreativeWork
De collectie objecten beschouwen we als werken (CreativeWork). 
![Werk model](./assets/work_model.jpg "Werk model")

## Person
![Person model](./assets/person_model.jpg "Person model")

