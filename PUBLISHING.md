# Publishing to PyPI

This project is configured to automatically publish to PyPI using GitHub Actions whenever a release is created.

## Setup Instructions

### 1. Configure PyPI Trusted Publishing (OIDC)

This workflow uses **OpenID Connect (OIDC)** for authentication, which is more secure than static API tokens.

**For PyPI (production):**
1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name:** `pytut`
   - **Owner:** `Manas-thakur`
   - **Repository name:** `python-tutorial`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
4. Create a release on GitHub to trigger the workflow and confirm the publisher

**For TestPyPI (optional, for testing):**
1. Go to https://test.pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name:** `pytut`
   - **Owner:** `Manas-thakur`
   - **Repository name:** `python-tutorial`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `testpypi`

### 2. Create a Release

To publish to PyPI:

```bash
git tag v2.0.0
git push origin v2.0.0
```

Then go to GitHub and create a release from that tag. The workflow will automatically:
- Build the distribution packages
- Check them with twine
- Publish to PyPI

### 3. Manual Testing

To test publishing to TestPyPI without creating a release:

1. Go to **Actions** tab in your GitHub repository
2. Select the **"Publish to PyPI"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. The workflow will publish to TestPyPI instead

### 4. Installation

Users can install your package with:

```bash
pip install pytut
```

Or directly run it:

```bash
pytut
pytut-cli
```

## Workflow Details

The `publish.yml` workflow:

- **Triggers:** 
  - Automatically on GitHub releases (published)
  - Manually via `workflow_dispatch`
  
- **Jobs:**
  1. `build` - Builds the distribution packages
  2. `publish-to-pypi` - Publishes to PyPI (on releases)
  3. `publish-to-test-pypi` - Publishes to TestPyPI (manual trigger only)

- **Security:** Uses OIDC trusted publishing, no static tokens needed

## Versioning

Update the version in `pyproject.toml`:

```toml
[project]
name = "pytut"
version = "2.0.1"  # Bump this
```

Then create and push a tag matching the version.

## Troubleshooting

**Publisher not found error:**
- Make sure the trusted publisher is configured on PyPI
- Verify the repository name and owner are exactly correct
- Environment names must match (`pypi` or `testpypi`)

**Build failures:**
- Run locally: `python -m build`
- Check: `twine check dist/*`

**Package not updating on PyPI:**
- PyPI doesn't allow re-uploading the same version
- Always bump the version in `pyproject.toml`
