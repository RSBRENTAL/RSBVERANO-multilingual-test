# Deployment-only files

Windows cannot keep `AGENTS.md` and `agents.md` as separate files in the same
directory. `AGENTS.md` is the internal repository guide; it must not be
published.

When creating a server package:

1. Copy the deployable tracked website files to a staging directory, excluding
   `.git`, every `AGENTS.md`, and the `deployment` directory.
2. Copy `deployment/agents-public.md` to `agents.md` at the staging root.
3. Create the ZIP from the contents of the staging root.
4. Verify that the ZIP contains `agents.md` and does not contain `AGENTS.md`,
   `agents-public.md`, or the `deployment` directory.

The resulting archive path must be `/agents.md`, which deploys as
`https://rentalscooterbarcelona.com/agents.md`.

PowerShell mapping command, run from the repository root after staging the
website:

```powershell
Copy-Item -LiteralPath deployment\agents-public.md -Destination $stagingRoot\agents.md
```
