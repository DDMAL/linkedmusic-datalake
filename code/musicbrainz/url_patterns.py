"""
This module contains regex patterns to match various external URLs
against their corresponding Wikidata IDs.
It is used to extract identifiers from URLs for properties in the MusicBrainz schema.

The regex patterns are designed to match specific URL formats for different databases
and extract the relevant identifier, which is then used as the value for the property.
The keys in the `DATABASES_REGEX` dictionary correspond to the database names in the mapping,
and the values are compiled regex patterns that will match URLs from those databases.
"""

import re

DATABASES_REGEX = {
    "geonames": re.compile(
        r"^https?:\/\/(?:www\.|geotree\.)?geonames\.org\/([1-9][0-9]{0,8})"
    ),
    "soundcloud": re.compile(r"^https?:\/\/soundcloud\.com\/([0-9A-Za-z/_-]+)"),
    "ytc": re.compile(
        r"^https?:\/\/\w+\.youtube\.com\/channel\/(UC[-_0-9A-Za-z]{21}[AQgw])"
    ),
    "ytv": re.compile(
        r"^https?:\/\/(?:www\.|m\.|music\.)?youtu(?:be\.com\/watch\?v=|\.be\/|be\/shorts\/|be\/live\/)([-_0-9A-Za-z]{11})"
    ),
    "ytp": re.compile(
        r"^https?:\/\/(?:(?:music|www|m)\.)?youtube\.com\/playlist\?list=((?:PL|OLAK|RDCLAK)[-_0-9A-Za-z]+)"
    ),
    "discogsa": re.compile(
        r"^https?:\/\/(?:www\.)?discogs\.com\/artist\/([1-9][0-9]*)"
    ),
    "discogsw": re.compile(
        r"^https?:\/\/(?:www\.)?discogs\.com\/(?:[a-z]+\/)?(?:[^\/]+\/)?master\/([1-9][0-9]*)"
    ),
    "discogsl": re.compile(
        r"^https?:\/\/(?:www\.)?discogs\.com\/(?:[\w\-]+\/)?label\/([1-9][0-9]*)"
    ),
    "vgmdbr": re.compile(r"^https?:\/\/vgmdb\.net\/album\/([1-9]\d*)"),
    "vgmdbl": re.compile(r"^https?:\/\/vgmdb\.net\/org\/([1-9]\d*)"),
    "bba": re.compile(
        r"^https?:\/\/(?:www\.)?bookbrainz\.org\/author\/([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})"
    ),
    "bbl": re.compile(
        r"^https?:\/\/bookbrainz\.org\/publisher\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    ),
    "imslp": re.compile(r"^https?:\/\/imslp\.org\/wiki\/(.+)"),
    "imdb": re.compile(
        r"^https?:\/\/(?:(?:www|m)\.)?imdb\.com\/(?:(?:search\/)?title(?:\?companies=|\/)|name\/|event\/|news\/|company\/|list\/)(\w{2}\d+)"
    ),
    "applea": re.compile(
        r"^https?:\/\/music\.apple\.com\/(?:\w+\/)?artist\/(?:\w+\/)?(?:id)?([1-9]\d*)"
    ),
    "appler": re.compile(
        r"^https?:\/\/music\.apple\.com\/(?:[a-z]{2}\/)?album\/(?:[^\/]+\/)?([1-9][0-9]*)(?:\?l=\w+-\w+)?"
    ),
    "applel": re.compile(r"^https?:\/\/music\.apple\.com\/label\/([1-9]\d*)"),
    "applet": re.compile(
        r"^https?:\/\/(?:geo\.)?music\.apple\.com\/(?:[a-z]+\/)*track(?:\/.+)?\/(?:id)?([0-9]+\?i=[0-9]+)"
    ),
    "viaf": re.compile(
        r"^https?:\/\/(?:www\.)?viaf\.org\/viaf\/([1-9]\d(?:\d{0,7}|\d{17,20}))($|\/|\?|#)"
    ),
    "lastfm": re.compile(
        r"^https?:\/\/(?:www\.)?last\.fm\/(?:[a-z]{2}\/)?music\/([^\/\?\#]+)$"
    ),
    "rymr": re.compile(
        r"^https?:\/\/rateyourmusic\.com\/release\/((?:single|album|comp|ep)\/[^\/]+\/[^\/]+)\/"
    ),
    "ryml": re.compile(r"^https?:\/\/rateyourmusic\.com\/label\/([a-z\d_-]+)/"),
    "ryma": re.compile(r"^https?:\/\/rateyourmusic\.com\/artist\/([^\s\/]+)"),
    "rymc": re.compile(
        r"^https?://(?:www\.)?rateyourmusic\.com\/concert\/([a-z0-9\-]+\/[a-z0-9\-]+)"
    ),
    "rymv": re.compile(r"^https?:\/\/rateyourmusic\.com\/venue\/([a-z_\d’-]+)"),
    "rymw": re.compile(r"^https?:\/\/rateyourmusic\.com\/work\/([^\/]+)"),
    "rymt": re.compile(r"^https?:\/\/rateyourmusic\.com\/song\/([^\s?&]+\/[^\s?&]+)"),
    "metalb": re.compile(
        r"^https?:\/\/(?:www\.)?metal-archives\.com\/bands\/[A-Za-z_]*\/([1-9][0-9]{0,9})"
    ),
    "metalr": re.compile(
        r"^https?:\/\/(?:www\.)?metal-archives\.com\/release\/view\/id\/(\d+)"
    ),
    "metall": re.compile(
        r"^https?:\/\/(?:www\.)?metal-archives\.com\/label\.php\?id=([1-9]\d*)"
    ),
    "metala": re.compile(
        r"^https?:\/\/(?:www\.)?metal-archives\.com\/artist\.php\?id=([1-9][0-9]*)"
    ),
    "sammler": re.compile(
        r"^https?:\/\/(?:www\.)?musik-sammler\.de\/artist\/0*([1-9]\d*)(?:[\/#?]|$)"
    ),
    "worldcat": re.compile(
        r"^https?:\/\/(?:id|entities)\.oclc\.org\/worldcat\/entity\/([^\.]+)"
    ),
    "bnf": re.compile(
        r"^https?:\/\/catalogue\.bnf\.fr\/ark:\/12148\/cb(\d{8,9}[0-9bcdfghjkmnpqrstvwxz])"
    ),
    "rism": re.compile(
        r"^https?:\/\/rism\.online\/((people|institutions|sources)\/(\d+))\/?$"
    ),
    "dnb": re.compile(
        r"^https?:\/\/d\-nb\.info\/gnd\/(1[012]?\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X])$"
    ),
    "loc": re.compile(
        r"^https?:\/\/id\.loc\.gov\/authorities\/(?:(?:name|subject)s\/)?((?:gf|n|nb|nr|no|ns|sh|sj)(?:[4-9][0-9]|00|20[0-2][0-9])[0-9]{6})(?:\.html)?"
    ),
}
