# timtec.net → WordPress migration

Prepared from Google Drive backup metadata and a live crawl of www.timtec.net.

## Backup located on Google Drive

- **Primary:** `site-www.timtec.net-20260829-220910.zip` (115 MB, Aug 29 2026)
- **Drive ID:** `1GimGMtrfljZTroIOvcOsiMPFfSNbleI-`
- See `backup/BACKUP-SOURCE.md`

## Generated import files (`output/`)

| File | Purpose |
| --- | --- |
| `timtec-wordpress-import.xml` | WordPress WXR import (250 pages/posts, draft status) |
| `content-inventory.csv` | Full URL/title/slug inventory from live site crawl |
| `redirects.csv` | 301 map from Joomla `.html` paths to WordPress slugs |
| `drive/referring-anchors.csv` | High-value inbound URLs from SEO data on Drive |

## Staging WordPress locally

```bash
cd wordpress-migration
docker compose up -d
open http://localhost:8080
```

1. Complete WordPress install at http://localhost:8080
2. **Tools → Import → WordPress** → upload `output/timtec-wordpress-import.xml`
3. Install **FG Joomla to WordPress** for full DB migration after extracting SQL from backup zip
4. Install **Redirection** plugin → import `output/redirects.csv`
5. Settings → Permalinks → **Post name**

## Full DB migration (recommended)

The WXR file captures HTML content from the live site. For users, menus, and media metadata, use the Joomla SQL inside the Drive backup:

```bash
# Download zip from Google Drive, then:
unzip site-www.timtec.net-20260829-220910.zip -d backup/extracted
./scripts/extract_joomla_db.sh backup/extracted
```

Fill credentials in `fg-joomla-import-config.json`, then run **Tools → Import → Joomla (FG)** in WordPress.

## Custom features to rebuild after import

- Chemical structure search
- Compound / SMILES / TimTec ID search (use `botproduct` catalog bot)
- Registered user database access (`/home/download-databases.html`, `/user/register.html`)
