# homkare

### Working with /backend directory.

Before starting on backend code change, always make sure to active local virtual environment. This allows the project's dependencies to be installed locally in the project folder, instead of globally.

```bash
source .venv/bin/activate
```

After activating the virtual environment, install app's standard dependencies.

Install [UV](https://docs.astral.sh/uv/) to manage python libraries.

```bash
uv sync
```

### Technical Notes

For styling follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
