# MusicBrainz contributor-role inventory

Inspected 20 October 2026 against the official MusicBrainz relationship pages linked below. These are **33 configuration entries** (16 recording, 17 release), not observed instance counts. The historical JSON dump is in Arbutus/Montreal and was unavailable in this checkout. Current API evidence is a separate, purposive pilot; it cannot date or characterize that dump.

Every RDF role points from the **recording or release to the artist**. MusicBrainz defines these relationship pairs in artist-first order: a recording/release record supplies `direction: backward`, and an artist record supplies `forward`. Names shared across the two endpoint pairs have different UUIDs. All listed source types allow start/end dates; their presence in a particular record is optional.

The predicate for each row is `https://linkedmusic.ca/terms/musicbrainz/relationship/{UUID}`. Labels, local definitions, endpoint types and the reviewed broader `P767` alignment live in [`relations.json`](../src/rdf_conversion_config/relations.json). These are LinkedMusic terms, not an official MusicBrainz RDF ontology. Definitions explain both supported and unsupported interpretations.

| RDF subject → object | Source name and definition | Stable type UUID | Permitted source attributes |
| --- | --- | --- | --- |
| recording → artist | [field recordist](https://musicbrainz.org/relationship/fc9b963a-29fa-4949-b22a-3bffd2440024) | `fc9b963a-29fa-4949-b22a-3bffd2440024` | none |
| recording → artist | [misc](https://musicbrainz.org/relationship/68330a36-44cf-4fa2-84e8-533c6fe3fc23) | `68330a36-44cf-4fa2-84e8-533c6fe3fc23` | task |
| recording → artist | [mastering](https://musicbrainz.org/relationship/30adb2d7-dbcc-4393-9230-2098510ce3c1) | `30adb2d7-dbcc-4393-9230-2098510ce3c1` | additional, assistant, associate, co |
| recording → artist | [recording](https://musicbrainz.org/relationship/a01ee869-80a8-45ef-9447-c59e91aa7926) | `a01ee869-80a8-45ef-9447-c59e91aa7926` | additional, assistant, associate, co, instrument, vocal |
| recording → artist | [balance](https://musicbrainz.org/relationship/0748fa55-56b5-4ad5-8ce8-15b97f82a0c2) | `0748fa55-56b5-4ad5-8ce8-15b97f82a0c2` | additional, assistant, associate, co, instrument, vocal |
| recording → artist | [booking](https://musicbrainz.org/relationship/b1edc6f6-283d-4e32-b625-b96cfb192056) | `b1edc6f6-283d-4e32-b625-b96cfb192056` | none |
| recording → artist | [mix](https://musicbrainz.org/relationship/3e3102e1-1896-4f50-b5b2-dd9824e46efe) | `3e3102e1-1896-4f50-b5b2-dd9824e46efe` | additional, assistant, associate, co, instrument, task, vocal |
| recording → artist | [sound](https://musicbrainz.org/relationship/0cd6aa63-c297-42ed-8725-c16d31913a98) | `0cd6aa63-c297-42ed-8725-c16d31913a98` | additional, assistant, associate, co, instrument, vocal |
| recording → artist | [mix-DJ](https://musicbrainz.org/relationship/28338ee6-d578-485a-bb53-61dbfd7c6545) | `28338ee6-d578-485a-bb53-61dbfd7c6545` | none |
| recording → artist | [audio director](https://musicbrainz.org/relationship/5de30d91-3b98-4fa6-9cd4-26d80959f540) | `5de30d91-3b98-4fa6-9cd4-26d80959f540` | assistant |
| recording → artist | [artists and repertoire](https://musicbrainz.org/relationship/8dc10cef-3116-4b3d-8e3e-33ffb84a97df) | `8dc10cef-3116-4b3d-8e3e-33ffb84a97df` | none |
| recording → artist | [photography](https://musicbrainz.org/relationship/a7e408a1-8c64-4122-9ec2-906068955187) | `a7e408a1-8c64-4122-9ec2-906068955187` | additional |
| recording → artist | [instrument technician](https://musicbrainz.org/relationship/e88fefc3-042b-4f28-83af-6a79793b630b) | `e88fefc3-042b-4f28-83af-6a79793b630b` | instrument |
| recording → artist | [engineer](https://musicbrainz.org/relationship/5dcc52af-7064-4051-8d62-7d80f4c3c907) | `5dcc52af-7064-4051-8d62-7d80f4c3c907` | additional, assistant, associate, co, executive, instrument, task, vocal |
| recording → artist | [audio](https://musicbrainz.org/relationship/ca8d6d99-b847-439c-b0ec-33d8a1b942bc) | `ca8d6d99-b847-439c-b0ec-33d8a1b942bc` | additional, assistant, associate, co, instrument, vocal |
| recording → artist | [remixer](https://musicbrainz.org/relationship/7950be4d-13a3-48e7-906b-5af562e39544) | `7950be4d-13a3-48e7-906b-5af562e39544` | additional, assistant |
| release → artist | [field recordist](https://musicbrainz.org/relationship/d92d4280-e288-4268-81ca-4c7252dfe7c3) | `d92d4280-e288-4268-81ca-4c7252dfe7c3` | none |
| release → artist | [transfer](https://musicbrainz.org/relationship/9fe3ca27-f9df-4e06-ab2d-84947f3f897e) | `9fe3ca27-f9df-4e06-ab2d-84947f3f897e` | additional, assistant, associate, co |
| release → artist | [mastering](https://musicbrainz.org/relationship/84453d28-c3e8-4864-9aae-25aa968bcf9e) | `84453d28-c3e8-4864-9aae-25aa968bcf9e` | additional, assistant, associate, co, pre, re |
| release → artist | [recording](https://musicbrainz.org/relationship/023a6c6d-80af-4f88-ae69-f5f6213f9bf4) | `023a6c6d-80af-4f88-ae69-f5f6213f9bf4` | additional, assistant, associate, co, instrument, vocal |
| release → artist | [balance](https://musicbrainz.org/relationship/97169e5e-c978-486e-a5ea-da353ca9ea42) | `97169e5e-c978-486e-a5ea-da353ca9ea42` | additional, assistant, associate, co, instrument, vocal |
| release → artist | [lacquer cut](https://musicbrainz.org/relationship/904e57f3-cbbc-43ab-8798-13e710e400d3) | `904e57f3-cbbc-43ab-8798-13e710e400d3` | none |
| release → artist | [booking](https://musicbrainz.org/relationship/b0f98226-7121-4db5-a69c-552e6d061da2) | `b0f98226-7121-4db5-a69c-552e6d061da2` | none |
| release → artist | [mix](https://musicbrainz.org/relationship/6cc958c0-533b-4540-a281-058fbb941890) | `6cc958c0-533b-4540-a281-058fbb941890` | additional, assistant, associate, co, instrument, task, vocal |
| release → artist | [sound](https://musicbrainz.org/relationship/271306ca-c77f-4fe0-94bc-dd4b87ae0205) | `271306ca-c77f-4fe0-94bc-dd4b87ae0205` | additional, assistant, associate, co, instrument, vocal |
| release → artist | [mix-DJ](https://musicbrainz.org/relationship/9162dedd-790c-446c-838e-240f877dbfe2) | `9162dedd-790c-446c-838e-240f877dbfe2` | medium |
| release → artist | [audio director](https://musicbrainz.org/relationship/4e088178-ea6f-4194-a801-10b4f0f03154) | `4e088178-ea6f-4194-a801-10b4f0f03154` | assistant |
| release → artist | [liner notes](https://musicbrainz.org/relationship/01323b4f-7aba-410c-8c91-cb224b963a40) | `01323b4f-7aba-410c-8c91-cb224b963a40` | additional, translator |
| release → artist | [instrument technician](https://musicbrainz.org/relationship/bd780597-0b67-4b97-a4a0-671a70e1182d) | `bd780597-0b67-4b97-a4a0-671a70e1182d` | instrument |
| release → artist | [audio](https://musicbrainz.org/relationship/b04848d7-dbd9-4be0-9d8c-13df6d6e40db) | `b04848d7-dbd9-4be0-9d8c-13df6d6e40db` | additional, assistant, associate, co, instrument, vocal |
| release → artist | [booklet editor](https://musicbrainz.org/relationship/74518a6b-589d-460e-8dd7-a8383851040a) | `74518a6b-589d-460e-8dd7-a8383851040a` | none |
| release → artist | [production coordinator](https://musicbrainz.org/relationship/65e417c8-c76b-4fef-af6d-6a5a515d181f) | `65e417c8-c76b-4fef-af6d-6a5a515d181f` | none |
| release → artist | [remixer](https://musicbrainz.org/relationship/ac6a86db-f757-4815-a07e-744428d2382b) | `ac6a86db-f757-4815-a07e-744428d2382b` | additional, assistant |

## Attribute definitions

These links identify the official attribute definitions. The converter preserves the attributes actually supplied, including unexpected attributes, rather than enforcing today’s list on an older dump.

- [additional](https://musicbrainz.org/relationship-attribute/0a5341f8-3b1d-4f99-a0c6-26b7f4e42c7f)
- [assistant](https://musicbrainz.org/relationship-attribute/8c4196b1-7053-4b16-921a-f22b2898ed44)
- [associate](https://musicbrainz.org/relationship-attribute/8d23d2dd-13df-43ea-85a0-d7eb38dc32ec)
- [co](https://musicbrainz.org/relationship-attribute/ac6f6b4c-a4ec-4483-a04e-9f425a914573)
- [executive](https://musicbrainz.org/relationship-attribute/e0039285-6667-4f94-80d6-aa6520c6d359)
- [instrument](https://musicbrainz.org/relationship-attribute/0abd7f04-5e28-425b-956f-94789d9bcbe2)
- [medium](https://musicbrainz.org/relationship-attribute/1f0299ce-dc34-30f1-b374-4749b30606e6)
- [pre](https://musicbrainz.org/relationship-attribute/288b973a-26ea-4880-8eca-45af4b8e8665)
- [re](https://musicbrainz.org/relationship-attribute/9b72452f-550e-4ace-93ed-fb8789cdc245)
- [task](https://musicbrainz.org/relationship-attribute/39867b3b-0f1e-40d5-b602-4f3936b7f486)
- [translator](https://musicbrainz.org/relationship-attribute/25dfb08e-9b99-44db-b30c-1d6ec6747af8)
- [vocal](https://musicbrainz.org/relationship-attribute/d92884b7-ee0c-46d5-96f3-918196ba8c5b)

## Interpretation and alignment

Each retained role describes a contribution from the artist to the recording/release, so its work-to-artist predicate is aligned with `wdt:P767` using `rdfs:subPropertyOf`. No role is equivalent to `P767`, and no reverse implication is declared. Generic engineering is not promoted to recording engineering. Photography and instrument maintenance do not imply performance. Deprecated recording mastering remains on the supplied recording.

Existing release photography uses a different Wikidata mapping and is outside this P767 pilot. Existing inverse `null` mappings outside the pilot remain unchanged. The pilot recognizes inverse records by UUID and emits the same work-to-artist role.

## Evidence and next snapshot check

The official definitions and six API responses used during this session are local artifacts under `/tmp/linkedmusic-preservation-2026-10-20/`; `definition-manifest.json` and `api-manifest.json` record URLs/checksums. Preserve those artifacts with the next audit snapshot if needed. They are not committed data.

When the stored dump is available, sample its recording, release (including embedded recordings), and inverse artist records. Compare UUIDs, directions, qualifier keys, and date precision with this inventory. Report missing IDs and unexpected directions as unresolved conversion evidence, not guessed roles. Measure each outcome with an explicit relationship denominator. See [the pilot model and commands](relationship_preservation.md).
