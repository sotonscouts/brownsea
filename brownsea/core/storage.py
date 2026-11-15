from whitenoise.storage import CompressedManifestStaticFilesStorage

# Where Vite writes the compiled frontend (`outDir` in vite.config.js), relative to the static root.
VITE_DIR = "dist/"


class StaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Production static files storage.

    Django renames collected files to include a hash (`main-CKSFW2-u.js` becomes `main-CKSFW2-u.2c9551de2c37.js`),
    but it leaves the names inside JavaScript imports alone. Vite's chunks import each other, and the entry file, by
    their own names, so the browser loads the entry under two URLs: once from the page's `<script>`, and again from a
    chunk's `import`. The entry then would run twice.

    Vite already puts a content hash in every file name, so its output is served as it is: copied and compressed,
    but not renamed.
    """

    def post_process(self, paths, dry_run=False, **options):  # noqa: FBT002
        frontend = {name: file for name, file in paths.items() if name.startswith(VITE_DIR)}
        others = {name: file for name, file in paths.items() if name not in frontend}

        yield from super().post_process(others, dry_run=dry_run, **options)

        if frontend and not dry_run:
            yield from self.post_process_with_compression((name, name, True) for name in frontend)

    def stored_name(self, name):
        if name.startswith(VITE_DIR):
            return name
        return super().stored_name(name)
