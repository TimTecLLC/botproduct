# timtec.net backup source (Google Drive)

Primary backup used for this migration package:

| Field | Value |
| --- | --- |
| File | `site-www.timtec.net-20260829-220910.zip` |
| Size | 115 MB (120,975,093 bytes) |
| Date | 2026-08-29 22:09 UTC |
| Drive file ID | `1GimGMtrfljZTroIOvcOsiMPFfSNbleI-` |
| Drive link | https://drive.google.com/file/d/1GimGMtrfljZTroIOvcOsiMPFfSNbleI-/view |

Additional backups in the same Drive folder:

- `site-www.timtec.net-20230211-192856.zip` (96 MB)
- `site-www.timtec.net-20231029-153616.zip` (101 MB)

## Expected contents inside the zip

Typical cPanel/JetBackup site archives for Joomla contain:

1. `public_html/` or domain root with Joomla files
2. `configuration.php` (Joomla DB credentials)
3. `administrator/`, `components/`, `templates/gantry/`
4. `mysql/` or `.sql` database dump

## Extract locally

Download the zip from Google Drive, then run:

```bash
cd wordpress-migration/backup
unzip site-www.timtec.net-20260829-220910.zip
./../scripts/extract_joomla_db.sh .
```

Use the extracted SQL file with the FG Joomla to WordPress plugin after WordPress is installed.
