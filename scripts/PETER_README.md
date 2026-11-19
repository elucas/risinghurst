# Peter and Barbara
Extracting data from *.pdf -> .txt -> .csv -> .html
191 pages across 83 files

## Scripts
Run the scripts in the following order to build up the data:

  $ uv run python build_csv.py 
  Wrote 641 rows to species.csv
  $ uv run python normalise.py 
  Updated 641 rows in species.csv
  $ uv run python build_references.py 
  Wrote 166 unique species to references.csv
