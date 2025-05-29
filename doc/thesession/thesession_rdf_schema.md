# Explanation of The Session's Data Structure and RDF Schema

This document is yet complete.


## I. How are Events different from Sessions?
Events are Irish music concert and festivals where the user is expected to listen. They have a fixed start date and end date (June 10th, 2006, 9:30pm – 11pm).

Sessions are "jam sessions", where the user is expected to bring an instrument and play along. Thesession.org usually indicates the day of the week when a session happens (e.g. Wednesday). It will remove the session once it is no longer active. 

## Schema of Events.CSV
events.csv contains all the live traditional Irish music events that thesession.org keeps track of.

- event_id is a URI of the format "https://thesession.org/events/{number}". It is the subject of all RDF triples created from this csv

- event is the name of the event (e.g. National Celtic Festival). We will it link it to event_id using rdfs:label, the standard predicate for "the label/name of a node". We should format it as "National Celtic Festival"@en to indicate that all label names from thesession.org are in English.

- dtstart and dtend are start time and end time of the event. P580 is the Wikidata start time property; P582 is the end time property. We store these as literals as xsd:dateTime, which is the standard datatype for dates.



- address is the string literal of the address. It is not reconciled

- As for location where the event took place: town is the city; area is the territory/province; country is the country