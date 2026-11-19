# Scientific name is the identity of a Species

Original Poster data names species by their Poster Name ("Fox"), and iNaturalist names them by scientific name. Wikipedia lookups based on common names drifted to the wrong page (Fox → the genus article). So every data source (poster records, observations, Wikipedia data, fragments) joins on the Scientific Name. Page slugs and common names are for display only. A hand-curated table (`wiki_custom.csv`, which gains a `scientific_name` column) maps each Poster Name to exactly one Scientific Name. That can be a genus or broader group when the poster was vague, rather than a guessed species.

## Consequences

- Linking old poster records to new iNaturalist observations depends on that mapping table being complete and correct. It's drafted from the iNaturalist taxa API and checked by hand.
- Species identified at genus level won't match species-level Observations.
