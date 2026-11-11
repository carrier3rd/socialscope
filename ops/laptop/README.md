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

## After a reboot (learned Nov 3, 2026)

The Nov 3 22:54 reboot upgraded the laptop to Ubuntu 24.04 (Python 3.11 -> 3.12), which broke every venv.
dgg-live crash-looped ("pip install websockets") until liveenv was rebuilt:
  mv liveenv liveenv.py311.bak && python3 -m venv liveenv && liveenv/bin/pip install websockets==17.4
A second reboot at 23:12 the same night upgraded again, to Ubuntu 26.04 (Python 3.14), and liveenv needed the
same rebuild (old copy liveenv.py312.bak). After any OS upgrade, check `liveenv/bin/python -c 'import websockets'`
first. ytenv and stenv are still on 3.11 and need the same rebuild before their next use.
The status servers (8765, 8766, 8767) are plain nohup http.server processes and don't survive a reboot:
  nohup python3 -m http.server <port> --directory ~/socialscope_data/<status dir> > ~/socialscope_data/<status dir>_server.log 2>&1 &
botfinds-weekly.service / .timer (added Nov 11, 2026): weekly Bot Bouncer status check for submitted bot finds,
Mondays 06:30, runs ops/botfinds_weekly.sh. Install: copy both into ~/.config/systemd/user/, daemon-reload, then
`systemctl --user enable --now botfinds-weekly.timer`. Log: ~/socialscope_data/botfinds_weekly.out.
