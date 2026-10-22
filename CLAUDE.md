@AGENTS.md

## Claude Code notes

- Start each lane in its own git worktree at `.claude/worktree/<lane>`, on the branch named in `AGENTS.md`. Remove it when the task is done (`AGENTS.md` → Worktrees).
- Before finishing a task, run the lane's checks (`invoke check` or the npm scripts) and report the real results.
- Name every subagent or parallel run with an Uzbek name, kept for the whole task (e.g. "Jasur (Claude) builds backend").
- Load the matching skill when it fits:
  - `django-patterns`, `django-tdd`, `django-security`, `docker-patterns` for the backend;
  - `react-patterns`, `react-testing`, `vite-patterns` for the frontend.
