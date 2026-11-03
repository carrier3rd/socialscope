# Laptop job scripts (copies)

The live copies run from ~/socialscope_data (queue scripts) and ~/.config/systemd/user (dgg-live.service).
These are copies so the repo shows how each job was launched; update them here when the live ones change.

- dgg_chat_queue.sh   RustleSearch DGG chat pull (stopped Nov 2: 200 requests/day limit)
- orl_queue.sh        OverRustle aggregation, first pass (12 channels, done Nov 2)
- orl2_queue.sh       second pass (the 11 archives added later, plus skips)
- orl_keep_queue.sh   5-channel rerun with --keep-file into orl_agg_keep
- dgg-live.service    standing read-only live chat logger (systemd --user, Restart=always, linger on)

Each queue script is launched as
  nohup systemd-inhibit --what=idle:sleep --mode=block --who=socialscope --why="..." ./<name>.sh > <name>.out 2>&1 &
and has a line in ~/socialscope_data/jobs.tsv.
