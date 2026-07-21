# Windows install commands and gotchas

## Protected locations

`~/.claude` (C:\Users\<user>\.claude) is protected - agents cannot mount or write it. Stage the finished package in the working directory and hand the user a one-liner. Never claim to have installed to ~/.claude directly.

## robocopy semantics (the /E vs /MIR lesson)

- `robocopy SRC DST /E` - MERGES. Existing files in DST that are not in SRC survive. This is how stale files from an old install haunt a new one (symptom: "why is this file in another language / where did this come from").
- `robocopy SRC DST /MIR` - MIRRORS. DST becomes exactly SRC; extras are deleted.

Rules: fresh install into an empty destination -> /E is fine. UPDATING an existing skill -> /MIR on that skill's folder. Restructuring (skills moved/nested) -> explicit Remove-Item of the old top-level folders, then copy. NEVER /MIR a shared parent folder like ~/.claude/skills itself - it would delete the user's other skills.

```powershell
# fresh install of staged skills (merge into skills dir)
robocopy "<staging>\skills" "$env:USERPROFILE\.claude\skills" /E

# update one skill in place (exact mirror of that folder only)
robocopy "<staging>\skills\<name>" "$env:USERPROFILE\.claude\skills\<name>" /MIR

# remove specific old folders before a restructured install
"<old1>","<old2>" | ForEach-Object { Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\$_" -ErrorAction SilentlyContinue }
```

Note robocopy exit codes 0-7 are success variants; only 8+ is failure.

## PATH for bundled binaries

```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$env:USERPROFILE\.claude\skills\<name>\bin", "User")
```

PATH changes need a NEW terminal. Give the user the verification command for after restart (e.g. `<tool> --version`).

## Compiling on Windows - the link.exe trap

`cargo install` (and other MSVC builds) fail with `link: extra operand ... Try 'link --help'` when GNU coreutils' `link` (Git Bash / MSYS on PATH) shadows MSVC's linker. The "install VS build tools" hint in the error is usually a red herring - check for the "extra operand" symptom first. Fix: use the prebuilt release binary instead (preferred), or build from a "x64 Native Tools Command Prompt".

## Verification after user runs commands

Ask for `dir` output or the tool's version string when something looks off - never assume the command worked. Common user-side misses: running the cleanup half but not the copy half of a two-part command; old terminal without the new PATH.
