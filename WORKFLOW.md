# WORKFLOW.md — Universal AI App Build Workflow

> A complete end-to-end guide for building any web app with AI assistance.
> Use this document with Claude Cowork, Claude Code, Codex, or any agentic
> AI tool. Stack assumption: Next.js 14 + Supabase + TypeScript.

---

## How to use this document

This WORKFLOW.md is a script for the AI — and a guide for you.

**If you are the developer:** Read Phase 0 to understand the workflow shape,
then hand this document to your AI tool and answer its questions as it walks
through the phases.

**If you are an AI agent reading this:** This is your operating procedure.
Follow each phase in order. Stop and ask the user when a phase requires
their input. Never skip phases. Generate the artifacts described in each
phase before moving to the next.

---

## Workflow at a glance

```
Phase 0 — Bootstrap     Run setup.sh, scaffold the project folder
Phase 1 — Align         Grill Me session → PRD
Phase 2 — Specify       Generate spec docs from PRD
Phase 3 — Plan          PRD → Epics → Features → Issues → Execution Plan
Phase 4 — Build         Worktrees in parallel per phase → PRs → Merge
Phase 5 — Ship          Final review → QA → Close sprint

./scripts/status.sh     Run at any point to see where every issue stands
```

Each phase has a fixed output (a file or folder of files) that becomes
input for the next phase. The artifacts are the contract between phases.

---

## Entry points

The workflow supports two entry points. The AI must determine which applies
before starting:

**Entry A — From an idea or napkin sketch (no PRD exists):**
Start at Phase 1. The AI runs the Grill Me session to produce a PRD.

**Entry B — User brings an existing PRD:**
Skip to Phase 2. The AI starts by generating spec docs from the existing PRD.

**Detection:** Check whether `issues/prd-*.md` exists in the project folder.
If yes → Entry B. If no → Entry A.

---

## Skills used in this workflow

All thirteen skills live in `.claude/skills/<name>/SKILL.md` and are
auto-discovered by both Claude Code and Codex (via a `.codex/skills`
symlink). Invoke each by typing `/<name>` as a slash command.

| Skill | Phase | Purpose |
|---|---|---|
| `/grill-me` | 1 | Interview the user until alignment is reached |
| `/write-prd` | 1 | Summarise the alignment session into a PRD |
| `/write-specs` | 2 | Generate docs/ from the PRD |
| `/write-system-specs` | 2 | Generate behavioural specs for complex systems in docs/systems/ |
| `/prd-to-epics` | 3 | Break PRD into 2–5 user-facing capability epics |
| `/epic-to-features` | 3 | Break each epic into 2–4 vertical slice features |
| `/feature-to-issues` | 3 | Break each feature into 1–4 atomic issues with TDD plans |
| `/plan-issues` | 3 | Build the DAG, group into phases, generate worktree-run.sh |
| `/implement` | 4 | Execute one issue with strict TDD (called by worktree-run.sh) |
| `/audit` | 4 | Post-implementation audit (called automatically) |
| `/resolve-conflicts` | 4 | Auto-resolve merge conflicts when a feature branch collides with newer main (called automatically by worktree-run.sh between audit and push) |
| `/review` | 5 | Human-facing code review on a diff |
| `/improve-architecture` | ongoing | Quarterly codebase health |
| `/debug` | ongoing | Diagnose stuck issues |

---

# Phase 0 — Bootstrap

> **Who does this:** You, with the AI guiding setup.
> **Output:** A project folder with all skills, scripts, and templates ready.
> **Time:** 10–15 minutes.

## Step 0.1 — Confirm the AI has the prerequisites

Before starting, verify these are installed on the machine:

```bash
# Required
node --version          # 20+
npm --version           # 10+
git --version           # 2.40+

# AI agents (install at least one)
which claude            # Claude Code CLI
which codex             # Codex CLI

# Recommended
which gh                # GitHub CLI for opening PRs
which supabase          # Supabase CLI for local dev
```

If anything is missing, install before continuing. The AI should print
install commands for any missing tool and wait for confirmation before
proceeding.

## Step 0.2 — Decide on the project name and location

The AI must ask the user:

1. **App name** — used for the folder name (will be slugified) and CLAUDE.md
2. **Parent directory** — where to create the folder (default: `~/projects`)

Once confirmed, navigate there:

```bash
cd ~/projects
```

## Step 0.3 — Run setup.sh

setup.sh is the canonical scaffold script. It must be available in the
parent directory (or downloaded from the workflow template repo).

```bash
chmod +x setup.sh
./setup.sh "Your App Name"
cd your-app-name
```

This creates:
- `CLAUDE.md` and `AGENTS.md` (coding standards)
- `.claude/skills/<name>/SKILL.md` (12 skills, auto-discovered by Claude Code)
- `.codex/skills` (symlink so Codex sees the same skills)
- `docs/` (6 spec template files)
- `issues/` (full hierarchy with STATUS.md placeholder)
- `scripts/` (once.sh, ralph.sh, status.sh, worktree-merge.sh)
- `.github/pull_request_template.md`

## Step 0.4 — Verify skills are discoverable

Open the AI tool from inside the project folder:

```bash
claude
# or
codex
```

Type `/help` and confirm all 13 custom skills appear in the list:
`grill-me, write-prd, write-specs, write-system-specs, prd-to-epics,
epic-to-features, feature-to-issues, plan-issues, implement, audit,
resolve-conflicts, review, improve-architecture, debug`

If any are missing, see Troubleshooting at the end.

## Step 0.5 — Initialise the actual app stack

For a Next.js + Supabase project, scaffold the app:

```bash
# Next.js with TypeScript, Tailwind, App Router
npx create-next-app@latest . \
  --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Supabase local dev
supabase init
supabase start
```

Note the Supabase output — copy the API URL, anon key, and service role key.

## Step 0.6 — Create .env.local

```bash
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
EOF
```

## Step 0.7 — Update CLAUDE.md module map

Open `CLAUDE.md` and update the "Module Map" section to match the actual
directory structure created by `create-next-app`. The defaults are correct
for a standard Next.js layout but verify.

## Step 0.8 — Initialise git and push

```bash
git init
git add .
git commit -m "chore: initial scaffold with workflow tooling"

# Create the GitHub repo (or use gh)
gh repo create your-app-name --private --source=. --remote=origin
git branch -M main
git push -u origin main
```

**Protect main on GitHub:**
- Settings → Branches → Add branch protection rule for `main`
- ☑ Require a pull request before merging
- ☑ Require status checks to pass

The worktree workflow depends on this — it pushes branches and expects
PRs as the merge gate.

## Step 0.9 — Verify feedback loops

```bash
npm run test        # placeholder, may have no tests yet
npm run type-check
npm run lint
```

All three must pass on a clean repo. If any fail, fix before Phase 1.
The AI's output quality is capped by the quality of these feedback loops.

**Phase 0 checklist:**
```
[ ] Project folder created
[ ] Next.js installed
[ ] Supabase local dev running
[ ] .env.local created
[ ] CLAUDE.md module map updated
[ ] Git initialised and pushed
[ ] main branch protected
[ ] All 12 skills discoverable in Claude Code (/help shows them)
[ ] npm run test, type-check, lint all pass
```

---

# Phase 1 — Align (Grill Me → PRD)

> **Who does this:** AI interviews user, then writes the PRD.
> **Output:** `issues/prd-[name].md`
> **Time:** 30–60 minutes depending on feature complexity.
> **Skip if:** A PRD already exists in `issues/` (Entry B).

## Step 1.1 — Check for existing PRD

The AI must first check:

```bash
ls issues/prd-*.md 2>/dev/null
```

- If a PRD exists → confirm with user whether to use it (skip to Phase 2)
  or write a new one
- If no PRD exists → continue with Step 1.2

## Step 1.2 — Optional: load a brief

If the user has notes, a client message, or a meeting transcript, load it:

```bash
cat > issues/clientbrief.md << 'EOF'
[paste the brief here]
EOF
```

## Step 1.3 — Run the Grill Me skill

In the AI tool, the user (or the AI orchestrator) types:

```
/grill-me
```

Then provides the idea description or pastes the brief contents.

**Behaviour the AI must follow:**

1. First, silently explore the codebase (using a sub-agent) and report a
   3-bullet summary of relevant existing code
2. Ask exactly ONE question at a time
3. For each question, provide a recommended answer
4. Cover at minimum:
   - **Data model** — new tables, columns, relationships, RLS policies
   - **Business logic** — edge cases, validation rules, error states
   - **User experience** — what the user sees, when, in what state
   - **Integration points** — which existing services/components are affected
   - **Out of scope** — what is explicitly NOT in this session
   - **Testing strategy** — how we will know it works
5. Continue until the user types `done` or `write the PRD`

**Tone:** direct and relentless. Surface uncomfortable assumptions.
Push back on vague answers.

## Step 1.4 — Write the PRD

When the user signals end of session, the AI runs:

```
/write-prd
```

This writes `issues/prd-[feature-name].md` containing:
- **Problem** — one paragraph
- **Solution** — one paragraph
- **User Stories** — all stories from the session
- **Acceptance Criteria** — specific, testable conditions
- **Data Model** — tables and relationships
- **Module Map** — which existing modules are modified, which are new
- **Implementation Decisions** — key decisions with rationale
- **Out of Scope** — explicit exclusions
- **Testing Strategy** — unit / integration / manual QA approach

## Step 1.5 — User reviews the PRD

The user does NOT need to read every word. They check three things only:

1. **Module Map** — does it list the right files?
2. **Out of Scope** — anything missing that should be excluded?
3. **Acceptance Criteria** — do these feel testable and concrete?

If those look right, confirm and commit:

```bash
git add issues/
git commit -m "plan: add PRD for [feature]"
git push
```

**Phase 1 checklist:**
```
[ ] Grill Me session completed (no early exit)
[ ] PRD written to issues/prd-[name].md
[ ] Module map reviewed and correct
[ ] Out of scope list reviewed
[ ] Acceptance criteria are specific and testable
[ ] PRD committed
```

---

# Phase 2 — Specify (Spec Documents)

> **Who does this:** AI drafts, user fills gaps and locks the docs.
> **Output:** All 6 files in `docs/` filled in and locked.
> **Time:** 20–40 minutes.

## Step 2.1 — Run the write-specs skill

In a fresh AI session (clear context first):

```
/write-specs issues/prd-[name].md
```

The AI reads the PRD and drafts all six spec documents:

- `docs/schema.md` — every table from the PRD with columns, indexes, RLS
- `docs/api-contracts.md` — every API route with Zod request schema and response shape
- `docs/auth.md` — auth method, roles, RLS summary, protected routes
- `docs/architecture.md` — system overview, services map, data flow
- `docs/decisions.md` — ADRs for each major Grill Me decision
- `docs/env.md` — every environment variable with example values

For anything the AI cannot determine from the PRD, it inserts:
```markdown
<!-- TODO: fill in before epics are created -->
```

## Step 2.2 — User fills the placeholders

The AI lists every TODO it inserted. The user opens each file and fills them:

```bash
# Common placeholders to fill
docs/schema.md      → confirm RLS policies, indexes
docs/auth.md        → confirm auth method, list protected routes
docs/api-contracts.md → confirm error response shapes
docs/env.md         → add third-party service keys (email, payments)
```

## Step 2.3 — Run write-system-specs

For any system in the PRD that is stateful, multi-actor, financially
sensitive, or conflict-prone (e.g. negotiation, payment, booking,
approval, subscription flows), generate a behavioural spec:

```
/write-system-specs issues/prd-[name].md
```

The skill auto-detects which systems need specs from the PRD. For each
one it creates `docs/systems/[system-slug].md` containing the state
machine, transition table, business rules, sequence diagrams, and edge
cases. The agent reads these during implementation so it knows exactly
how each system is supposed to behave.

Review every TODO the skill flags, fill them in, then continue.

## Step 2.4 — Lock the docs

Once all TODOs are filled across docs/ and docs/systems/:

```bash
git add docs/
git commit -m "docs: write spec documents from PRD"
git push
```

These files are now **source of truth**. The agent will read them when an
issue references them and implement to match exactly.

**Phase 2 checklist:**
```
[ ] All 6 docs/ files generated
[ ] All <!-- TODO --> placeholders filled in docs/
[ ] Every PRD table has a docs/schema.md entry
[ ] Every user story has a docs/api-contracts.md route
[ ] Auth flows fully specified
[ ] System specs generated for every complex/stateful system
[ ] All <!-- TODO --> placeholders filled in docs/systems/
[ ] Schema and API gaps flagged by write-system-specs resolved
[ ] docs/ and docs/systems/ committed
```

---

# Phase 3 — Plan (Epics → Features → Issues → Execution Plan)

> **Who does this:** AI generates each level, user reviews and pushes back.
> **Output:** Populated `issues/epics/`, `issues/features/`, `issues/open/`,
> plus `issues/EXECUTION_PLAN.md` and `scripts/worktree-run.sh`.
> **Time:** 1–3 hours depending on PRD scope.

## Step 3.1 — Break PRD into epics

```
/prd-to-epics issues/prd-[name].md
```

The AI proposes 2–5 epics. Each epic must be a **user-facing capability area**,
not a technical layer.

**What good epics look like:**
- E01 Authentication and User Profile
- E02 Course Discovery and Enrolment
- E03 Lesson Player

**What bad epics look like (push back on these):**
- E01 Database Schema  ← technical layer, not capability
- E02 API Layer        ← same problem
- E03 Frontend         ← same problem

If the AI proposes horizontal/technical epics, instruct it:

> These look like technical layers, not user-facing capabilities.
> Rewrite as capability areas — what does the user get from each epic?

On approval, files are written to `issues/epics/E[N]-[slug].md`.

## Step 3.2 — Break each epic into features

Run once per epic:

```
/epic-to-features issues/epics/E01-[slug].md
```

The AI proposes 2–4 vertical slice features per epic. Each feature must
touch at least two layers (e.g. DB + service, or service + UI) and
produce a visible/testable result.

**The vertical slice test for each feature:**
> "If I merge only this feature, can I open the app and see or test something?"

If the answer is no, push back:

> Feature F01 has no visible output.
> Merge the schema, service, and UI badge into one vertical slice.

Repeat for every epic. Files are written to:
`issues/features/E[N]-[epic-slug]/F[N]-[feature-slug].md`

## Step 3.3 — Break each feature into issues

Run once per feature:

```
/feature-to-issues issues/features/E01-[epic]/F01-[feature].md
```

The AI reads the feature, parent epic, PRD, and relevant docs/ files,
then generates 1–4 issue files containing:
- Reference Docs (which docs/ files apply)
- Acceptance Criteria
- Files to Modify (full paths)
- Step-by-step TDD Implementation Plan
- Git branch and commit format

**What to push back on:**

If test assertions are vague:
> Test descriptions are too vague. Each Test N needs an exact assertion —
> specific function name, specific input, specific expected return value.

If an issue modifies more than 6 files:
> This issue is too large. Split into two —
> one for the schema and service, one for the route and UI.

If the first issue in a feature isn't visible:
> Issue 001 is schema + service only. Merge the dashboard badge into
> this issue so the first issue is a complete vertical slice.

Repeat for every feature in every epic. Issues are written to
`issues/open/[NNN]-[slug].md`.

Commit after each epic:

```bash
git add issues/
git commit -m "plan: features and issues for E[N]"
git push
```

## Step 3.4 — Generate the execution plan

Once all issues are written:

```
/plan-issues
```

The AI:
1. Reads every issue's `**Blocked by:**` field
2. Builds the dependency DAG
3. Groups issues into phases (every issue in a phase can run in parallel)
4. Writes `issues/EXECUTION_PLAN.md` with a Mermaid DAG diagram and phase tables
5. Writes `scripts/worktree-run.sh` with phase arrays populated

**Review the plan before continuing:**
- Open `EXECUTION_PLAN.md` and look at the Mermaid diagram (renders on GitHub)
- Check that issues which modify the same files are NOT in the same phase
  (conflict risk)
- Check Human-in-loop issues are flagged correctly
- Verify no circular dependencies were reported

If something looks wrong, fix the `**Blocked by:**` field in the relevant
issue files and re-run `/plan-issues`.

## Step 3.5 — Snapshot initial status

```bash
./scripts/status.sh --write
```

Writes `issues/STATUS.md` showing every issue as either `open` (no blockers)
or `blocked` (waiting on others). Commit:

```bash
git add issues/EXECUTION_PLAN.md issues/STATUS.md scripts/worktree-run.sh
git commit -m "plan: execution plan with DAG and worktree script"
git push
chmod +x scripts/worktree-run.sh scripts/worktree-merge.sh
```

**Phase 3 checklist:**
```
[ ] All epics written to issues/epics/
[ ] All features written to issues/features/
[ ] All issues written to issues/open/
[ ] Each issue has Reference Docs section
[ ] Each issue has Implementation Plan with specific Test assertions
[ ] First issue in every feature produces visible output
[ ] No issue modifies more than 6 files
[ ] EXECUTION_PLAN.md generated and reviewed
[ ] DAG diagram looks correct
[ ] No same-phase issues touch same files
[ ] STATUS.md snapshotted
```

---

# Phase 4 — Build (Worktrees → PRs → Merge)

> **Who does this:** AI agents in parallel worktrees. User reviews PRs.
> **Output:** All issues merged to main, branches cleaned up.
> **Time:** Varies — typically 10–30 minutes per issue, all parallel.

## Step 4.1 — Verify the loop is healthy

Before running a full phase, run a single issue sequentially:

```bash
./scripts/once.sh
```

This picks the highest-priority unblocked issue and runs it without a
worktree. Watch the output — the agent should:

1. Read the Epic, Feature, and Reference Docs
2. Create a feature branch
3. Write a failing test (Red)
4. Implement code to pass it (Green)
5. Repeat for each Implementation Plan step
6. Run the full feedback loop (test, type-check, lint)
7. Run the self-audit
8. Commit and push

If anything goes wrong, use `/debug` to diagnose:

```
/debug

[paste the error output]
```

## Step 4.2 — Run Phase 1 in parallel worktrees

```bash
./scripts/worktree-run.sh 1
```

Every Phase 1 issue runs as its own git worktree simultaneously. No cap on
parallelism. Each worktree:
1. Creates `feature/<slug>` from main in `../.worktrees/<slug>/`
2. Runs the agent with the issue + Epic + Feature + spec docs as context
3. Audits the diff in a fresh AI session
4. If `[APPROVED]`: fetches `origin/main` and attempts a merge. If newer
   commits on main produce conflicts, invokes the `/resolve-conflicts`
   skill with the conflict diff + issue spec as context — the skill
   classifies each region (additive / same-line / structural), applies
   file-type-specific rules (Prisma schemas, NestJS module decorators,
   PROGRESS.md, lockfiles, package.json), and verifies with
   `prisma validate` + `pnpm test` + `pnpm type-check` + `pnpm lint`
   before staging. If the skill returns `[ESCALATE: ...]` the worktree
   is left in mid-merge state for human resolution (exit 4).
5. Pushes the branch
6. Auto-opens a PR via `gh pr create` — title sourced from the issue's
   `# Issue NNN: ...` heading, body from its `## Goal` section. Best
   effort; failures are logged but do not fail the worktree.

When all worktrees finish, you'll see:

```
✓ APPROVED + PR opened (3): review the auto-opened PRs
✗ AUDIT FAILED (1): see ../.worktrees/<slug>.audit.log
⚠ CONFLICTS UNRESOLVABLE (0): mid-merge state left in worktree;
  see ../.worktrees/<slug>.resolve.log
```

## Step 4.3 — Check status

```bash
./scripts/status.sh
```

Shows each issue's current state with an action-needed summary at the
bottom telling you exactly what to do next.

## Step 4.4 — Handle FAILED or BLOCKED worktrees

**AUDIT FAILED:**
```bash
cat ../.worktrees/<slug>.audit.log    # read what failed
cd ../.worktrees/<slug>
claude "Fix these audit failures: [paste CHANGES REQUIRED section]"
cd -
# Re-audit
ISSUE_FILE=$(cat issues/open/<NNN>-*.md)
SPECS=$(cat docs/*.md)
DIFF=$(git diff main...feature/<slug>)

# Build the audit prompt with all context embedded
{
  cat .claude/skills/audit/SKILL.md
  echo ""
  echo "---"
  echo "ISSUE:"
  echo "$ISSUE_FILE"
  echo ""
  echo "SPEC_DOCS:"
  echo "$SPECS"
  echo ""
  echo "DIFF:"
  echo "$DIFF"
} | claude -p > ../.worktrees/<slug>.audit.log
grep "APPROVED" ../.worktrees/<slug>.audit.log
(cd ../.worktrees/<slug> && git push)
```

**BLOCKED:**
```bash
# Fix the issue file (usually missing file in "Files to Modify")
code issues/open/<NNN>-<slug>.md
# Rebuild the worktree
git worktree remove ../.worktrees/<slug> --force
git branch -D feature/<slug>
./scripts/worktree-run.sh 1   # reruns the phase, finished worktrees skip
```

**CONFLICTS UNRESOLVABLE (exit 4):**
The `/resolve-conflicts` skill escalated. The worktree is mid-merge with
conflict markers still in place. Resolve manually:
```bash
cat ../.worktrees/<slug>.resolve.log   # read the [ESCALATE: ...] reason
cd ../.worktrees/<slug>
git diff --name-only --diff-filter=U   # list conflicted files
# Resolve each file by hand (the skill couldn't classify intent —
# usually a same-line edit where both sides changed the same logic)
# When resolved:
pnpm test && pnpm type-check && pnpm lint
git add <resolved-files>
git commit --no-edit                   # finish the merge
git push origin feature/<slug>
gh pr create --base main --head feature/<slug> --title "..." --body "..."
cd -
```
Common causes that require human intent: same-line logic edits, spec-doc
divergences (`docs/**/*.md`), `package.json` semver-incompatible bumps.

## Step 4.5 — Review and merge each branch

PRs are already open (auto-created by `worktree-run.sh` after the
`[APPROVED]` audit). For each APPROVED branch:

```bash
# Optional structured human review on top of the audit
git diff main...feature/<slug> | claude /review

# Manual QA in the running app
npm run dev

# List the auto-opened PRs for this phase
gh pr list --search "head:feature/" --state open
```

Then on GitHub, for each auto-opened PR:
1. Review the diff, the audit log, and (if any) the resolve log
2. **Squash and merge**

Merge ALL Phase 1 PRs before moving to Phase 2.

> The `gh pr create` step that previous workflows ran manually is now
> handled inside `worktree-run.sh` so you only ever review-and-merge.
> If a PR is missing (e.g. gh wasn't authenticated when the worktree
> finished), open it manually with `gh pr create --base main --head
> feature/<slug>`.

## Step 4.6 — Clean up and update status

```bash
./scripts/worktree-merge.sh 1
./scripts/status.sh --write
```

Cleans up Phase 1 worktrees, deletes local branches, moves issue files to
`issues/done/`, updates `STATUS.md`.

## Step 4.7 — Repeat for each phase

```bash
./scripts/worktree-run.sh 2
./scripts/status.sh
# fix failures → review → open PRs → merge on GitHub
./scripts/worktree-merge.sh 2
./scripts/status.sh --write
# repeat...
```

## Step 4.8 — Handle Human-in-loop issues

Issues marked `Human-in-loop` in the execution plan cannot be automated.
After the phase they depend on is fully merged:

```bash
git checkout -b feature/<NNN>-<slug>
# Implement manually, or run once.sh which will pick it up
./scripts/once.sh
git push -u origin feature/<NNN>-<slug>
# Open PR → review → merge on GitHub
mv issues/open/<NNN>-<slug>.md issues/done/
git add issues/ && git commit -m "chore: close #<NNN>" && git push
```

**Phase 4 checklist:**
```
[ ] All phases run (worktree-run.sh per phase)
[ ] All audit logs show [APPROVED]
[ ] All PRs merged on GitHub (Squash and merge)
[ ] All phases cleaned up (worktree-merge.sh per phase)
[ ] All issue files in issues/done/
[ ] issues/STATUS.md shows all issues as ✅ merged
[ ] npm run test passes on main
```

---

# Phase 5 — Ship (Final Review & Close Sprint)

> **Who does this:** You.
> **Time:** 30–60 minutes for a typical sprint.

## Step 5.1 — Final status check

```bash
./scripts/status.sh
```

Confirm all issues are merged. The action-needed line should read either
`🎉 All issues merged!` or list any remaining items.

## Step 5.2 — Manual QA on main

```bash
git checkout main && git pull
npm install && npm run dev
```

Walk through every user story in the PRD. For each acceptance criterion:
- [ ] Happy path works end-to-end
- [ ] Error states handled (try invalid input)
- [ ] Loading states exist
- [ ] Empty states handled
- [ ] Looks correct on mobile and desktop

## Step 5.3 — Generate next-sprint issues from QA

QA always finds things. For each finding, create a new issue file in
`issues/open/`. These become the next sprint's work.

## Step 5.4 — Update CHANGELOG and tag

```bash
# If you maintain a CHANGELOG.md
echo "## v0.X.0 - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "Closed: $(ls issues/done/ | wc -l) issues" >> CHANGELOG.md
git add CHANGELOG.md
git commit -m "chore: changelog for v0.X.0"
git tag -a v0.X.0 -m "Sprint complete"
git push --tags
```

**Phase 5 checklist:**
```
[ ] Status shows all merged
[ ] Manual QA completed on main
[ ] New issues created from QA findings
[ ] CHANGELOG updated
[ ] Version tagged
```

---

# Generate the project-specific MIGRATION_GUIDE.md

> **When to do this:** After Phase 0 setup is complete, before handing
> the project to another developer or AI tool.

The MIGRATION_GUIDE.md is a per-project document that explains exactly
how to continue the workflow from wherever it is now. It's tailored to
the specific project (uses the actual project name, branch names, and
folder paths).

## When the AI should generate it

Generate `MIGRATION_GUIDE.md` whenever any of these are true:

- Setup is complete and someone else needs to continue the workflow
- The project is being handed to a different AI tool (e.g. Cowork → Claude Code)
- The user wants to step away and come back later with a clear roadmap
- After Phase 1 PRD exists but before Phase 4 implementation

## How to generate it

The AI should write `MIGRATION_GUIDE.md` to the project root with this structure:

````markdown
# Migration Guide — [Project Name]

> Continue the AI-assisted build workflow for [Project Name].
> Current state: [phase X complete, phase Y in progress].

## What exists right now

[Inventory of completed artifacts:]
- ✅ Project scaffolded (CLAUDE.md, .claude/skills/, scripts/)
- ✅ PRD: issues/prd-[name].md
- ✅ Spec docs: 6 files in docs/, all TODOs filled
- ✅ Epics: N files in issues/epics/
- ⏳ Features: N of M epics broken down (E01, E02 done; E03+ pending)
- ⏳ Issues: only E01 features have issue files
- ❌ Execution plan: not yet generated

## Where to continue

You are at Phase [N], Step [N.N]. The next action is [specific command].

## Step-by-step continuation

[Numbered steps for the AI to follow, starting from the current state.
Each step says: what to type, expected output, what to commit.]

### Step 1 — Generate features for remaining epics

For each epic that doesn't have a features/E[N]-[slug]/ subdirectory:

```
/epic-to-features issues/epics/E[N]-[slug].md
```

Repeat for E03, E04, E05.

After all features are written:
```bash
git add issues/features/
git commit -m "plan: features for remaining epics"
git push
```

### Step 2 — Generate issues per feature
[...continue numbered steps through to merged Phase N...]

## Decisions already made (do not re-litigate)

[Pull from docs/decisions.md and PRD Implementation Decisions section]

## Quick reference

[All slash commands, scripts, and prompts the AI will need.
Copy from the relevant phase sections above.]

## Troubleshooting

[Project-specific issues encountered so far. Common ones:]
- "Skill not found" → restart Claude Code so it re-scans .claude/skills/
- "Worktree exists" → git worktree remove --force then retry
- "Audit fails on security every time" → see CLAUDE.md routing handler template

## Files to migrate (if reopening in a new chat)

[List of files in /mnt/user-data/outputs/ from the original conversation
and where each should land in the project folder.]
````

## What the AI must include

When generating MIGRATION_GUIDE.md, the AI must:

1. **Inventory the current state.** Run `ls issues/`, `ls issues/epics/`,
   `ls issues/features/*/`, `ls issues/open/`, `ls issues/done/` and
   record what exists.
2. **Determine the current phase and step.** Use the "Where to continue"
   logic: PRD missing → Phase 1; PRD exists but docs/ has TODOs → Phase 2;
   docs/ locked but epics empty → Phase 3.1; etc.
3. **List remaining steps explicitly.** Don't say "continue with Phase 3".
   Say "run /epic-to-features for E03, E04, E05 in that order; commit
   after each".
4. **Pull project-specific decisions.** Read docs/decisions.md and the
   PRD's Implementation Decisions section. List them so the next AI
   doesn't re-debate settled questions.
5. **Include the troubleshooting that's been encountered so far.** If
   the project hit any specific friction (a skill that needed restarting,
   a worktree conflict, etc.), document the resolution.
6. **Make it self-contained.** Someone should be able to read only this
   file (plus the project folder) and continue the work. Reference
   WORKFLOW.md for general guidance, but the migration guide should
   contain everything project-specific.

---

# Quick Reference

## Slash commands

| Command | When to use |
|---|---|
| `/grill-me` | Start of every new feature or PRD |
| `/write-prd` | After alignment is reached |
| `/write-specs <prd-file>` | After PRD is confirmed |
| `/write-system-specs <prd-file>` | After /write-specs — for every complex/stateful system |
| `/prd-to-epics <prd-file>` | After spec docs and system specs are locked |
| `/epic-to-features <epic-file>` | Once per epic |
| `/feature-to-issues <feature-file>` | Once per feature |
| `/plan-issues` | After all issues are written |
| `/implement` | (Called automatically by once.sh / worktree-run.sh) |
| `/audit` | (Called automatically inside each worktree) |
| `/resolve-conflicts` | (Called automatically by worktree-run.sh on merge conflict) |
| `/review` | Pipe a git diff in for human review |
| `/debug` | When agent is stuck |
| `/improve-architecture` | Quarterly health check |

## Scripts

| Command | When to use |
|---|---|
| `./scripts/once.sh` | Verify one issue runs cleanly |
| `./scripts/worktree-run.sh [N]` | Run all Phase N issues in parallel |
| `./scripts/worktree-merge.sh [N]` | Cleanup after Phase N PRs are merged |
| `./scripts/ralph.sh` | Sequential fallback (no worktrees) |
| `./scripts/status.sh` | Print live issue status |
| `./scripts/status.sh --write` | Update STATUS.md and commit |

## Push-back prompts

**Horizontal epics:**
> These are technical layers, not user capabilities. Rewrite as
> user-facing capability areas.

**Horizontal features:**
> This feature has no visible output. Merge it with the next feature
> into a single vertical slice.

**Vague implementation plan:**
> Test assertions are too vague. Each Test N needs the exact function
> name, input, and expected return value.

**Issue too large:**
> This issue touches too many files. Split into two: one for
> [schema + service], one for [route + UI].

**Agent modifying wrong files:**
> Stop. You are outside scope. Only modify files listed in
> ## Files to Modify.

**Agent skipped TDD:**
> You wrote implementation code before a failing test. Delete the
> implementation, write the failing test first, confirm it fails,
> then re-implement.

---

# Troubleshooting

### "Slash commands not found"

Skills must be at `.claude/skills/<name>/SKILL.md` (folder per skill).
Check:
```bash
ls .claude/skills/grill-me/SKILL.md
```
If missing, re-run setup.sh. If present, restart Claude Code so it
re-scans the skills directory.

### "Codex doesn't see the skills"

Verify the symlink:
```bash
ls -la .codex/skills    # should show: skills -> ../.claude/skills
```
If broken, recreate it:
```bash
rm -rf .codex/skills && mkdir -p .codex && ln -s ../.claude/skills .codex/skills
```

### "Tests pass before any implementation"

The agent cheated on TDD. Add to CLAUDE.md:
```markdown
## Test Integrity
If a test passes before implementation code exists, the test is wrong.
Stop, diagnose why, fix the test so it fails correctly, then implement.
```

### "Agent keeps running out of context"

The issue is too large. Split it. One issue should complete well within
80k tokens.

### "Audit fails on security every time"

Add a route handler template to CLAUDE.md:
```markdown
## Route Handler Template
Every route handler must:
1. Parse and validate input with Zod
2. Get session with getServerSession()
3. Return 401 if no session
4. Call service method
5. Return structured response
```

### "Worktree conflict — already exists"

Previous run was interrupted. Clean up:
```bash
git worktree remove ../.worktrees/<slug> --force && git worktree prune
git branch -D feature/<slug>
```

### "Conflict resolution escalated"

The `/resolve-conflicts` skill found a region it couldn't classify (usually
a same-line edit where the agent can't tell whose intent should win, or a
spec-doc divergence between `docs/**/*.md` on both sides). The worktree is
left in mid-merge state. Check the reason:
```bash
cat ../.worktrees/<slug>.resolve.log     # ends with [ESCALATE: <file>:<reason>]
cd ../.worktrees/<slug>
git status                                # shows files still marked UU
```
Resolve the flagged file by hand using the spec doc as ground truth.
Re-run `pnpm test && pnpm type-check && pnpm lint` before committing
the merge. Do not re-run the worktree — the implementation work is
already done; you only need to finish the merge:
```bash
git add <resolved-files>
git commit --no-edit
git push origin feature/<slug>
```

### "PR not auto-opened after a successful worktree run"

Check `gh` is authenticated in the shell that runs `worktree-run.sh`:
```bash
gh auth status
```
If the worktree pushed the branch but `gh pr create` failed, you'll see
`PR creation skipped` in `../.worktrees/<slug>.log`. Open manually:
```bash
gh pr create --base main --head feature/<slug>
```

### "I'm not sure what to do next"

Run `./scripts/status.sh`. The summary line at the bottom always names
the single most important next action.

---

# Appendix: Tooling Reference

## Stack

- **Frontend:** Next.js 14 (App Router), React 18
- **Backend:** Supabase (Postgres, Auth, Storage)
- **Language:** TypeScript (strict mode)
- **Testing:** Vitest + Testing Library
- **Styling:** Tailwind CSS

## File hierarchy

```
project-root/
├── CLAUDE.md                  ← coding standards, module map
├── AGENTS.md                  ← Codex equivalent
├── .claude/skills/            ← 12 skills, auto-discovered
├── .codex/skills              ← symlink to .claude/skills
├── docs/                      ← spec documents (source of truth)
│   ├── schema.md
│   ├── api-contracts.md
│   ├── auth.md
│   ├── architecture.md
│   ├── decisions.md
│   └── env.md
├── issues/
│   ├── prd-[name].md          ← PRD per feature
│   ├── epics/                 ← E[N]-[slug].md
│   ├── features/              ← E[N]-[epic]/F[N]-[feature].md
│   ├── open/                  ← [NNN]-[slug].md (agent picks here)
│   ├── done/                  ← merged issues
│   ├── discovered/            ← agent-found bugs
│   ├── EXECUTION_PLAN.md      ← DAG + phase plan
│   ├── STATUS.md              ← lifecycle tracker
│   └── merge-log.md           ← merge history
├── scripts/
│   ├── once.sh                ← single-issue test run
│   ├── ralph.sh               ← sequential AFK loop
│   ├── status.sh              ← live status tracker
│   ├── worktree-merge.sh      ← cleanup after PR merge
│   └── worktree-run.sh        ← (generated by /plan-issues)
├── .github/
│   └── pull_request_template.md
└── ../.worktrees/             ← parallel git worktrees during Phase 4
    ├── <slug>/
    ├── <slug>.log
    └── <slug>.audit.log
```

## Idea Tree (5-level hierarchy)

```
Idea
  └── PRD                                  (1 file)
        └── Epic                           (2-5 per PRD)
              └── Feature                  (2-4 per epic)
                    └── Issue              (1-4 per feature)
```

Each level reads its parent. The agent receives Issue + Feature + Epic +
spec docs as context when implementing.

## When to use each entry point

**Entry A (Grill Me):** Start here for any new product or feature where
you don't have a clear written spec yet.

**Entry B (existing PRD):** Start at Phase 2 if you already have a
written PRD, design doc, or spec from another source.

---

*This WORKFLOW.md is a living document. Update it when you discover what
works and what doesn't in your specific stack.*
