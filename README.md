1. Run `time bash discover_csv.sh` first (a couple of times)
2. Include those generated `.csv` to `pcunix_uptimes_viz.py` in `csv_files_to_plot`
3. Run `python pcunix_uptimes_viz.py`


## Results

(as of June, 7th 2025)

- Nodes ranges from `pcunix16.fing.edu.uy` to `pcunix144.fing.edu.uy` totalling in `144-16+1=129` nodes
- Of those 129 nodes, 51 were down or unreachable and 78 were up. I.e., 60% of the nodes were up.
- Majority of the CPUs are either i3-9100F (4c/4t) or i3-4150 (2c/4t) while a minority are i3-10100F (4c/8t) or i3-12100 (4c/8t).
- Overall, all nodes have 16 GiB of RAM, but the ones equipped with i3-4150 have 8 GiB of RAM.
