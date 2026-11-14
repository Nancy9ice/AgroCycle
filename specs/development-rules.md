# AgroCycle — Development Rules

These rules apply to everyone who changes this repository: the team, and any AI coding assistant working on a team member's behalf. The goal is to keep a 6-person, 2-day build coordinated and its progress visible.

The rule that matters most: **track progress in the roadmap, task by task, before moving on.**

## 1. Before you start: clarify role and phase

Before any implementation, state two things:

1. **Your role:** `de`, `ds1`, `ds2`, `be`, `fe` or `f` (data engineer, data scientists 1 and 2, backend, frontend, farmer).
2. **The roadmap phase and task** you are working on now (see `specs/roadmap.md`), for example "Phase 3, DE: extract and clip CDL".

Then:
- Check the **progress tracker** at the top of `specs/roadmap.md`. Do not take a task that is already `In progress` for another role-task.
- Check the phase's **dependencies**. Do not start a task whose upstream work is not `Done`, unless your feature spec explicitly says you will work against an agreed mock or contract (e.g. the frontend on mocked JSON).
- Set the task to `In progress` in the tracker, with your role, before you begin.

Work on **one phase task at a time**.

## 2. Write a feature spec for every phase task you implement

Every implemented phase task needs a feature spec folder:

```
specs/features/YYYY-MM-DD-role-feature-name/
  plan.md
  requirements.md
  validation.md
```

**Naming:** `YYYY-MM-DD-role-feature-name`
- `YYYY-MM-DD`: the date the spec is created.
- `role`: one of `de`, `ds1`, `ds2`, `be`, `fe`, `f`. The role identifies who owns the spec, so no personal name is used.
- `feature-name`: short, lowercase, hyphen-separated.
- Example: `2026-11-14-de-cdl-extraction`.

Copy the templates from `specs/features/_template/`. Write all three files **before** you implement, and keep them short.

| File | What it contains |
|---|---|
| `plan.md` | The roadmap phase and task it implements; the approach; files and tables it will create or change; steps in order; dependencies on other roles and the interfaces it relies on; risks; the size budget if it touches data. |
| `requirements.md` | What must be true when it is done: inputs and outputs (with schemas and units), acceptance criteria that can be tested, the PRD requirement IDs it covers (FR-xx, NFR-xx), the roadmap exit check it satisfies, evidence-type labels, scale and limitations to preserve. |
| `validation.md` | How each requirement will be verified: tests, data-integrity checks, `make check`, hand-checks and what evidence will be kept. A results section, filled in after implementation. |

If your work changes an interface another role depends on (a table, endpoint, file or schema), tell that role.

## 3. Implement only what the spec says

- If the scope or approach changes during implementation, **update the spec**, then continue.
- Keep changes small and focused on the one phase task.
- Follow `specs/tech-stack.md`. Raise any deviation with the team before using it.

## 4. After the task is done: update the roadmap before moving on

When the phase task is finished, and **before starting the next task**:

1. Fill in the **results** section of `validation.md`: what was run, what passed, what did not, and where the evidence is.
2. Update the **progress tracker** in `specs/roadmap.md`:
   - set the status (see below),
   - add the date and your role,
   - link the feature spec folder.
3. If the phase's exit check is met, say so in the tracker note.

This is mandatory. A task is not done until the roadmap shows it.

**Status values**

| Status | Meaning |
|---|---|
| `Not started` | Nobody has claimed it. |
| `In progress` | Claimed, with a role. A feature spec exists. |
| `Blocked` | Waiting on something. State what, and who owns it. |
| `Done` | Implemented, validated per `validation.md`, results recorded, and the exit check is met. |
| `Dropped` | Deliberately not done. State the reason (e.g. HLS adds nothing beyond CDL). |

Do not mark `Done` if validation failed or was skipped. Say so honestly in the tracker note instead.

## 5. Git workflow

- **Always create a branch.** Never commit or push directly to `main`.
- Name the branch after the feature spec, e.g. `feature/2026-11-14-de-cdl-extraction`.
- One feature spec per pull request. The PR includes the spec folder and the roadmap status update.
- No review approval is required to merge. Before merging, make sure there are **no conflicts**:
  - update your branch with the latest `main` and resolve any conflicts,
  - re-run your validation (and `make check` once it exists) after resolving them,
  - confirm the roadmap tracker still shows the correct status.
- The tracker table is edited by everyone, so change **only your own task's row** to keep merge conflicts small.
- Write clear commit messages. Do not commit secrets or large data (see `.gitignore`).

## 6. Quality and honesty rules (apply to every task)

- Run `make check` (schema checks, post-load assertions, tests) before marking a data task `Done`, once it exists.
- Label every output with its evidence type, scale and limitations.
- Missing or unsupported data is `unknown`, never silently neutral or favourable.
- Do not claim results the evidence does not support (see PRD §4.4 and the mission principles).
- Raw data goes to S3 with a manifest and checksum. Do not commit raw or large data to git.
- Credentials go in a local `.env`, never in git.

## 7. Quick checklist

1. State role and phase task.
2. Check the tracker and dependencies. Mark `In progress`.
3. Write the feature spec (`plan.md`, `requirements.md`, `validation.md`).
4. Implement on a branch.
5. Run the validation, and record the results in `validation.md`.
6. Update the roadmap tracker (your row only).
7. Update your branch with `main`, resolve conflicts, and merge the PR. Only then move to the next task.
