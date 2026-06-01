# UI/UX Design Skills for Claude Code

Two complementary skills that turn a PRD into a clickable HTML prototype, with a rigorous design spec as the bridge.

- **`ui-ux-spec`** — Reads a PRD, asks clarifying questions, produces a comprehensive UI/UX design specification at `docs/design/ui-ux-spec.md`. The spec covers navigation system, screen inventory, component library, design tokens, state coverage, accessibility, responsive behavior, motion, and copy. Becomes the source of truth for UI construction.

- **`ui-prototype`** — Reads the spec (or any spec following the same template), produces a self-contained `prototype.html` file with every screen, working navigation, mock data, and a state-switcher overlay so you can preview empty/loading/error/populated states. No build step required.

## Workflow

```
PRD → ui-ux-spec → docs/design/ui-ux-spec.md → ui-prototype → prototype.html
                              ↓                                       ↓
                  source of truth for build           preview before build
```

1. Drop your PRD in the project (typically `docs/prd.md`).
2. Run a prompt like *"create a UI design spec for this PRD"*. The `ui-ux-spec` skill activates, asks 8–15 clarifying questions, produces the spec.
3. Run *"build a clickable HTML prototype from the design spec"*. The `ui-prototype` skill activates, reads the spec, produces `prototype.html`.
4. Open the HTML file in a browser, click through, validate.
5. Iterate on the spec, regenerate the prototype as needed.
6. Hand the spec (not the prototype) to your build agent as the build source of truth.

## Installation

### Personal install (available in all projects)

Unzip the contents into `~/.claude/skills/`:

```bash
# macOS / Linux
unzip ui-ux-skills-claude-code.zip -d ~/.claude/skills/

# Windows (PowerShell)
Expand-Archive ui-ux-skills-claude-code.zip -DestinationPath "$HOME\.claude\skills\"
```

Verify the folder structure:

```bash
ls ~/.claude/skills/ui-ux-spec/
# Should show: SKILL.md  references/

ls ~/.claude/skills/ui-prototype/
# Should show: SKILL.md  references/
```

### Project install (shared with anyone who clones the repo)

Unzip into your repo's `.claude/skills/` instead:

```bash
unzip ui-ux-skills-claude-code.zip -d .claude/skills/
git add .claude/skills/
git commit -m "Add UI/UX design skills"
```

### Verify installation

Start (or restart) a Claude Code session in any project and run:

```
/skills
```

You should see `ui-ux-spec` and `ui-prototype` listed.

## Removing or disabling

Remove:

```bash
rm -rf ~/.claude/skills/ui-ux-spec ~/.claude/skills/ui-prototype
```

Temporarily disable a skill (rename so Claude Code ignores it):

```bash
mv ~/.claude/skills/ui-ux-spec ~/.claude/skills/_ui-ux-spec
```

## Recommended: add a hint to `CLAUDE.md`

Once installed, drop this into your project's `CLAUDE.md` so future sessions automatically use the spec as the UI source of truth:

```markdown
## UI/UX

The UI source of truth lives at `docs/design/ui-ux-spec.md`. When implementing
or modifying any UI, read the spec first and adhere to the navigation system,
component library, design tokens, and state coverage defined there. To validate
a design change visually, regenerate `prototype.html` from the spec.
```

## File structure

```
ui-ux-spec/
├── SKILL.md
└── references/
    ├── clarifying-questions.md     # 41-question bank with recommended defaults
    ├── uiux-fundamentals.md        # 20 non-negotiable principles
    ├── spec-template.md            # The 17-section spec skeleton
    └── navigation-patterns.md      # Deep reference on nav paradigms, back behavior, anti-patterns

ui-prototype/
├── SKILL.md
└── references/
    ├── scaffold.html               # Starter HTML with Tailwind + Alpine + prototype shell
    ├── shell-template.html         # Prototype shell (device frame, state switcher, jumper, notes)
    ├── mock-data-patterns.md       # Realistic mock data guide (no Lorem ipsum)
    ├── navigation-implementation.md # Hash routing, back stack, tab stacks, modals
    └── component-patterns.md       # Tailwind patterns for button, modal, sheet, toast, switch, etc.
```

## Tips

- The `ui-ux-spec` skill **always asks clarifying questions before generating**. If you want to skip, answer "use defaults" once and it will apply all recommended defaults and document them as assumptions.
- The `ui-prototype` skill is **read-only on your real source code** — it only writes `prototype.html`. Safe to run any time.
- Both skills produce **markdown that diffs cleanly in git**, so spec changes are reviewable in PRs.
- The prototype uses CDN-loaded Tailwind and Alpine.js — works offline once cached but needs internet on first load.

## License

Use, modify, and share freely.
