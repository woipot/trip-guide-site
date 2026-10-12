# Preview and publish

**Local preview** (once, before publishing):
1. `.claude/launch.json` in the working dir: `{"version":"0.0.1","configurations":[{"name":"site","runtimeExecutable":"python3","runtimeArgs":["-m","http.server","8765"],"port":8765}]}` and start it with the browser preview tool.
2. The main file has no `<!doctype>`/charset (the Artifact service adds the skeleton). For local viewing open `index.html`, the standalone copy the build writes next to it. `guide.html` and `phrases.html` are complete documents.
3. `html{scroll-behavior:smooth}` makes scripted scrolls animate — use `scrollTo({top, behavior:'instant'})` before screenshots. Browsers cache 404s: add `?v=2` when a file appeared after a failed load.
4. Check: no horizontal scroll at phone width, one option click changes the sticky total, `#g-<id>` opens a guide chapter, no console errors. Delete `.claude/` afterwards.

**Publish** (Artifact tool):
- `file_path` = the main file; `files` = `guide.html`, `phrases.html`, every `img/*.jpg` and `img/g/*.jpg` the build used (`trip/used_images.json`). Pass `icon` on the first publish only.
- The main page is served as **`index.html`** — that's why the sub-pages' menus link to `index.html`. Do not upload the local standalone `index.html` itself.

**Without the Artifact tool** (or for GitHub Pages / any static host): publish `index.html`, `guide.html`, `phrases.html` and `img/` as they are — the links already match.
- Upload in batches of ≤ ~45 files per call (big single publishes can fail with ECONNRESET); later calls to the same file_path add to the files already there.
- Removing a photo: map its path to `null`.
- Verify with `action: "list", scope: "files", url: …` that pages and all images are present.
- The artifact is private; tell the user to share it via the page's Share menu if a travel companion should see it.
