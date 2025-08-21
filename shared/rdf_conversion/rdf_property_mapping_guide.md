# Mapping against Wikidata properties using prop_cli.py

This short guide explains how to choose the most appropriate Wikidata property when mapping dataset relations. The guide assumes that you are doing mapping with the help of `prop_cli.py`. Nevertheless, all the steps can be replicated through navigating the Wikidata GUI (it just would be less convenient).

This guide will likely be merged into the [RDF conversion guideline Wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/RDF-Conversion-Guidelines) after the pull request. We still need to clarify how documentation is to be organized.

# 1. Mapping relations to Wikidata Properties

## 1.1 The Rule of Thumb

- Whenever possible, we should rely on how Wikidata properties are used, and not as much on how they are defined.
- Example:
  - Suppose you're trying to find a Wikidata property to describe the relationship between a software and the person who designed it.
  - You may hesitate between `creator(P170)` and `designed by(P287)` — just by looking at their definitions, you cannot tell which is more appropriate.
  - Nevertheless, you should choose `creator(P170)`, because that is the predicate used between `Linus Torvalds(Q34253)` and `Linux (Q388)`.

## 1.2 Running prop_cli.py

`prop_cli.py` is a simple CLI tool that can make property reconciliation less tedious:

- It removes the need to navigate Wikidata GUIs. You can work on property mapping without leaving your IDE much.

- You can start `prop_cli.py` by running:

```bash
python {path/to/prop_cli.py}
```

- Assuming your working directory is the repository root, the command would be:

```bash
python shared/prop_cli.py
```

You should see the prompt:

```bash
Enter a term, two terms (comma-separated), or a flag (--q, --r), or 'exit':
```

## 1.3 Decision Making Process

Once you have `prop_cli.py` running, here is the general guideline on how you should make each property mapping decision.

For each decision:

1. If you are truly clueless about which Wikidata property to use, find an example value in the dataset and type `--r {value}`.

- Example:
  - I have no clue how to map The Global Jukebox societies to their respective "continent".
  - I type `--r africa` in the console.
  - A list of all Wikidata properties used with `Africa(Q15)` is printed to the console.
  - I can look through this list and choose the best fitting property (i.e. `indigenous to(P2341)`).

2. If you know a good example of the relationship you're trying to map, type the two entities involved in this relationship, separated by a comma.

- Example:
  - I am not sure what property to use to map a jazz artist onto their work (are they performer or composer?). However, I know that the relation between Charlie Parker and Anthropology is a good example of this relationship.
  - I type `charlie parker, anthropology jazz` (if I don't type "jazz", "anthropology" would match onto the academic discipline)
  - Both `Anthropology(Q574394)  composer(P86)  Charlie Parker(Q103767)` and `Anthropology(Q574394)  performer(P175)  Charlie Parker(Q103767)` are printed to the console.
  - I know that I should use both `P86` and `P175`.
  - I can type `dizzy gillespie, night in tunisia` to double check.
  - It returns the same result. I am confident in my mapping.

3. If you know (or can guess) what the Wikidata property is named but don't remember the PID, type the property name.

- Example:
  - Type `occupation` in the console.
  - The first result is `occupation(P106)`.
