# 01-17-2025

**Lab Meeting**

**RISM Data Processing**:
- Converted raw RDF (.ttl) data to human-readable format and analyzed schema
- Successfully reconciled "Person" and "Institution" subjects using OpenRefine
- Planned: Implement merge script for CSV and RDF data integration

# 01-20-2025

> Remote work day

**RISM Data Processing**:
- Completed CSV-RDF merge function implementation after extensive debugging
- Deployed data to Virtuoso
- Next phase: Scale up processing and enhance reconciliation coverage

# 01-24-2025

**Lab Meeting**

**RISM Data Processing**:
- Investigating BNode recognition issue

# 01-27-2025

**RISM Data Processing**:
- Status: BNode recognition debugging unsuccessful
    - Challenge: Multiple BNodes sharing subject + predicate pairs cause ambiguity
    - Current limitation: Unable to map CSV structure to RDF effectively
- Alternative approach implemented:
    - Direct CSV-to-dictionary-to-RDF conversion
    - Using 32-bit string BNode IDs
    - Trade-off: Successful implementation but potentially reduced method generality
- Open for further optimization and discussion

# 02-03-2025
**Graph splitting**
- Implement graph splitting algorithm on a small data set

# 02-07-2025
**Lab Meeting**

- Still trying to split the graphs
- Taking too much RAM and time, even on the Lab Mac. Trying a different approach
- Should we use OpenRefine API?

# 02-10-2025
**Remote**

**OpenRefine API**:
- Reading OpenRefine source code on GitHub to get familiar with it
- Written in Java, so direct Python usage is not possible
- Exploring alternative Python libraries
- Reviewing OpenRefine reconciliation documentation for Python-compatible libraries
- Tested [https://github.com/preftech/reconciliation]

# 02-14-2025
**Lab Meeting**

**OpenRefine API**:
- Reading the OpenRefine documentation
- Testing [https://github.com/PaulMakepeace/refine-client-py/]

# 02-17-2025
**Remote**

**OpenRefine API**:
- Reading the OpenRefine documentation
- Unable to find a valid way to integrate OpenRefine in the script

# 02-21-2025

**Lab Meeting**

**Wikidata API**:
- Reading the W3C reconciliation documentation format
- Applying tests to our local RISM data dump
- More details in [https://github.com/DDMAL/linkedmusic-datalake/issues/230]

# 02-24-2025

**Remote**

**Reconciliation**:
- Regenerated the RDF graph according to the refined reconciliation mapping
- More precise reconciliation needed
- Comparing pros and cons of OpenRefine reconciliation versus Wikidata API reconciliation
- More details in [https://github.com/DDMAL/linkedmusic-datalake/issues/230]

# 02-28-2025

**Lab Meeting**

- Testing the auto-reconciling script
- New approach: trying force splitting graph to OpenRefine

# 03-10-2025

**Remote**

- Debugging finished after the test for auto-reconciling script failed, continue to test

# 03-14-2025

**Lab Meeting**

- Figuring out which method is not valid, thinking of new methods.
- Read about OpenRefine RDF Skeleton and RDF-transform extensions. 
- Start testing this process of OpenRefine outputting RDF.

# 03-19-2025

**Remote**

- Applied mapping to raw file, convert blank nodes to URIs for OpenRefine to keep its original nodeID.
- Testing entire process, cleaning the RDF Skeleton for RISM database
- Writing a document about the entire process, including screen shots of detailed instructions.