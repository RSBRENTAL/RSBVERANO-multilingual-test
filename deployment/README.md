# Deployment-only files

Windows cannot keep `AGENTS.md` and `agents.md` as separate files in the same
directory. `AGENTS.md` is the internal repository guide; it must not be
published.

When creating a server package:

1. Prefer an explicit allowlist of public website content instead of copying
   the repository indiscriminately.
2. Copy only deployable public website files to a staging directory.
3. Never include internal or development-only content, including:
   - `.git/`
   - `seo-rank-tracker/`
   - every internal `AGENTS.md`
   - `deployment/`
   - `.env` files
   - credentials, API keys, tokens, or other secrets
   - internal reports
   - backups
   - test/development artifacts
4. Copy `deployment/agents-public.md` to `agents.md` at the staging root.
5. Create the ZIP from the contents of the staging root.
6. Before deployment, verify that the ZIP:
   - contains the public `agents.md`;
   - does not contain any `AGENTS.md`;
   - does not contain `agents-public.md`;
   - does not contain `deployment/`;
   - does not contain `seo-rank-tracker/`;
   - does not contain `.git/`, `.env` files, credentials, tokens, internal
     reports, backups, or development artifacts.

The resulting archive path must be `/agents.md`, which deploys as
`https://rentalscooterbarcelona.com/agents.md`.

PowerShell mapping command, run from the repository root after staging the
website:

```powershell
Copy-Item -LiteralPath deployment\agents-public.md -Destination $stagingRoot\agents.md
```
