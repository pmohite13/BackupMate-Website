# BackupMate website

The public site for BackupMate: `https://backupmate.buzzneuron.com`.

It is static HTML. Pages are written in `src/`, built by `build.py` into `public/`,
and `public/` is committed, so the host only serves files. There is nothing to
install beyond the Python already on the machine.

## Layout

| Path | What it is |
| --- | --- |
| `site.json` | **Every fact the site states**: prices, support address, refund period, legal name. Edit here, never in a page. |
| `src/layout.html` | The header and footer every page shares |
| `src/pages/` | One file per page: a few `key: value` lines, `---`, then HTML |
| `src/assets/` | The stylesheet and icon. No scripts, no fonts, nothing loaded from elsewhere |
| `build.py` | `src/` + `site.json` → `public/` |
| `release.py` | Records a release: version, checksums, download links |
| `preview.py` | Serves `public/` at `http://localhost:8080` the way the real host will |
| `public/` | The built site. **Generated: do not edit by hand** |

## Everyday use

```
python build.py        # build, warning about anything missing
python preview.py      # look at it
python build.py --strict   # before publishing: refuses to build with gaps
```

`--strict` deletes `public/` when it fails, deliberately, so that a draft with
"[legal name to be confirmed]" on its Terms page cannot be deployed by mistake.

## Before the site goes live

`site.json` has values that only the owner can supply. Until they are filled in,
`build.py --strict` fails and the pages show an obvious gap.

All of them are filled in as of 11 October 2026. A value can be marked as an
unapproved suggestion by starting it with `CONFIRM`; `--strict` then refuses.

No release is recorded yet, so the download page says the installers are on
their way. That does not stop the site being published.

The site names no grievance officer, by the owner's decision. India's e-commerce
rules ask sellers for one; whether they apply to this business is a question for
the lawyer reviewing the legal pages.

The legal pages (`src/pages/legal/`) are drafts written to be clear and fair.
**They have not been reviewed by a lawyer.** Have that done before taking money.

When Paddle is added for sales outside India, its terms require the site to say
that Paddle is the merchant of record for those sales; add that to the terms of
sale and the refund policy at that point.

## Hosting (Cloudflare Workers, static assets)

The site is served by a Cloudflare Worker named `backupmate-web`, which holds
the custom domain `backupmate.buzzneuron.com`. It is built from THIS repository:

- Worker → Settings → Build → Git repository: `pmohite13/BackupMate-Website`
- Production branch: `main`. Build command: none. Deploy command:
  `npx wrangler deploy`. Root directory: `/`.

`wrangler.jsonc` tells that deploy which Worker to update and that the site is
in `public/`, with `/pricing` serving `pricing.html` and `404.html` for anything
missing. Do not rename the Worker there: a different name deploys a different
Worker, and the live site silently stops changing. (This happened once: the
Worker was first connected to a one-off copy of this repository, so merges here
changed nothing.)

To check a merge went live, look for a new entry on the Worker's Deployments
page with the merge's commit, then load `/version.json`.

Every other branch is built too, as a **preview** (`npx wrangler preview`, the
"Previews Base" build settings): its own address, not the live site. Open a
PR's preview to see a change before merging it.

**The installers do not go in this repository.** Each is larger than the 25 MB
per-file limit for static assets. Put them in a Cloudflare R2 bucket (free at this
size, no download charges) with a custom domain such as
`backupmate-downloads.buzzneuron.com`, in a folder per version.

## Publishing a release

The order matters. Every installed BackupMate server reads
`https://backupmate.buzzneuron.com/version.json` once a day and, when the
version there is newer than its own, sends its administrator to `/download`.
**That address is compiled into every installed copy and must keep working.**

1. Build the two MSIs in the product repository.
2. Upload them to the downloads bucket as
   `<version>/BackupMate-<version>.msi` and
   `<version>/BackupMateServer-<version>.msi`.
3. Record the release, against the same files you uploaded:

   ```
   python release.py 0.4.11 --client C:\BackupMate\dist\BackupMate.msi --server C:\BackupMate\dist\BackupMateServer.msi --base-url https://backupmate-downloads.buzzneuron.com/0.4.11
   ```

   Add `--signed` once the installers carry a code-signing signature; the
   download page then drops its SmartScreen warning.
4. `python build.py --strict`, then `python preview.py` and **click both download
   links** to prove they work.
5. Commit and merge to `main`. The site, the checksums and `version.json` go live
   together.

To withdraw a release, record the previous one again and publish; servers stop
announcing the withdrawn version within a day.

## Changing a price

Edit `plans` in `site.json`, build, commit. The home page, the pricing page and
anything else that quotes it change together.
