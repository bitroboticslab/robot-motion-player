# OSS Sync Audit

- Date/time: 2026-04-17T20:33:28+08:00
- Dry-run build command:
  - `cd /home/junhang/packages/robot-motion-player && python scripts/oss_sync/build_staging.py --src /home/junhang/packages/robot-motion-player --staging /home/junhang/packages/robot-motion-player-oss-stage --allowlist scripts/oss_sync/allowlist.txt --denylist scripts/oss_sync/denylist.txt --dry-run`
- Dry-run apply command:
  - `cd /home/junhang/packages/robot-motion-player && python scripts/oss_sync/apply_to_oss.py --staging /home/junhang/packages/robot-motion-player-oss-stage --oss /home/junhang/packages/robot-motion-player-oss --dry-run`
- Result summary: success; build `report.json` copied count = 12, apply `apply_report.json` copied count = 0 (dry-run).
