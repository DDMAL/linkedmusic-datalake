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