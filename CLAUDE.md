@AGENTS.md

## Claude Code notes

- Start each lane in its own git worktree at `.claude/worktree/<lane>`, on the branch named in `AGENTS.md`. Remove it when the task is done (`AGENTS.md` → Worktrees).
- Before finishing a task, run the lane's checks (`invoke check` or the npm scripts) and report the real results.
- **Delegation:** you own your lane. In the backend and frontend lanes only (**never design**), send simple, exactly specified tasks to Antigravity with the `antigravity-delegate` skill. Follow `AGENTS.md` → Delegation, which overrides the skill:
  - worktree at `.claude/worktree/ag-<lane>-<task>`;
  - a full diff review plus checks before merging;
  - complex tasks stay with you.
- **Testing:** test every feature as soon as it's finished (`AGENTS.md` → Testing), before starting the next one.
- **Merging:** you may merge PRs that meet `AGENTS.md` → Merging. Lane owners merge Antigravity branches into their lane branch; the main session merges lane PRs into `main`.
- Name every subagent or parallel run with an Uzbek name, kept for the whole task (e.g. "Jasur (Claude) builds backend").
- Load the matching skill when it fits:
  - `django-patterns`, `django-tdd`, `django-security`, `docker-patterns` for the backend;
  - `react-patterns`, `react-testing`, `vite-patterns` for the frontend.
