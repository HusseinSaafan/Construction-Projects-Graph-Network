# Project Linking Using a Graph Network Approach

This document describes a phased solution for linking duplicate or related construction projects in a database.

Because project records come from multiple sources, the same real-world construction project can appear as multiple entries. The goal is to reduce this noise and build a clearer, more complete project-level view.

The approach is demonstrated using a regional pilot dataset, then scaled to the full dataset.

## Core Features

The following features are used to build graph relationships:

1. `project_name` -> text embeddings
2. `project_description` -> text embeddings
3. `longitude`/`latitude` -> coordinate pair `[long, lat]`
4. `end_date` -> encoded date feature
5. `work_scope` -> phase-based filter and matching context

## Output Table Structure

Each record in the output contains:

1. `features` -> observation-level features used for matching
2. `Community_ID` -> primary location-based community ID
3. `Sub_Community_ID` -> project-level cluster ID within each community
4. `observation_ID` -> unique source record ID (node ID)

### Field Definitions

#### `features`
- `longitude`/`latitude` are used to create edges for primary communities.
- `project_name`, `project_description`, and `end_date` are used to create edges for sub-communities (representing actual construction projects).
- `work_scope` controls which records are considered in each phase.

#### `Community_ID`
- A location-based cluster ID.
- Records are grouped when coordinates match or fall within a configured geospatial radius.
- This is the first-level signal that records may refer to the same real project context.

#### `Sub_Community_ID`
- A finer-grained cluster ID within each `Community_ID`.
- Built from similarity on project name, description, and end date.
- Represents the actual linked construction project.

#### `observation_ID`
- The unique project instance from the source database.
- Observations are graph nodes used to form both communities and sub-communities.

## Solution Logic (Phased Execution)

The solution is executed in multiple phases, with thresholds adjusted by phase intent.

### Pre-phases
- extract df from database

- extract for df fields description (documentation of the engineers for each field):
  
### Phase 1 - Build Primary Communities by Location

- Build a graph where each node is an `observation_ID`.
- Create edges based on geospatial proximity (`longitude`/`latitude`).
- Generate `Community_ID` clusters for records sharing the same location or within a configured distance limit.

Output fields:
- `Community_ID`
- `observation_ID`
- `features`

### Phase 2 - Build Sub-Communities for New Construction

- Filter records to `work_scope = "New Construction"`.
- Within each `Community_ID`, build sub-communities using name, description, and end-date similarity.
- Assign `Sub_Community_ID` to represent the actual construction project.

Output fields:
- `Community_ID`
- `Sub_Community_ID`
- `observation_ID`
- `features`

Matching strategy:
- Use relatively lower thresholds and wider ranges than later phases to maximize recall for new-construction grouping.

### Phase 3 - Link Maintenance to Existing New Construction Clusters

- Filter to `work_scope IN ("New Construction", "Maintenance")`.
- Attempt to link currently unlinked maintenance observations to existing sub-communities.
- Increase strictness compared with Phase 2, with stronger emphasis on end-date alignment.

Rationale:
- Many maintenance records represent warranty or post-delivery activity for a new-construction project.
- These records remain within the same `Community_ID` created in Phase 1.

### Phase 4 - Handle Renovation and Maintenance Relationships

- Filter to `work_scope IN ("Renovation", "Maintenance")`.
- Link renovation-to-renovation first.
- Then evaluate renovation-to-maintenance links where relevant.

Constraint:
- All sub-community linking remains within the existing `Community_ID` from Phase 1.

### Phase 5 - High-Precision Maintenance-to-Maintenance Linking

- Link `work_scope = "Maintenance"` records to each other.
- Apply stricter thresholds and narrower acceptance ranges to prioritize precision.


## Notes and Risks

- Additional reliable features would significantly improve linkage quality.
- Many sub-communities may contain a single node; this is expected for unique or weakly matched projects.
- Many records are missing coordinates; these should be geocoded from address where possible.
- Records missing both usable coordinates and usable address cannot be placed in location communities.
- Phase logic assumes work-scope labels are correct. Early checks may show some misclassified records, so work-scope quality should be validated before threshold tuning.



