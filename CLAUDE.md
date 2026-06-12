# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. SQL And Migration Discipline

**Every model/schema change must be treated as a database state transition, not just a code change.**

When adding or changing SQL, ORM fields, Alembic migrations, seed data, or query projections:
- Check whether the target table may already exist in user databases. If yes, migrations must be idempotent where practical: inspect table/column/index existence before adding or mutating.
- Never assume editing an already-applied migration will update existing databases. If `alembic_version` has reached that revision, add a new repair/forward migration instead.
- Verify both sides: the ORM/query expects the column, and the real database has it. A successful `upgrade head` is not enough if the revision was previously marked applied.
- After migration, inspect `alembic_version` and the actual table columns/indexes involved in the change.
- For non-null new columns on existing tables, provide a safe default/backfill path before enforcing `nullable=False`.
- For seed/menu/permission data, use insert-if-missing/update-if-needed logic so repeated migrations do not create duplicates.
- Before finishing, run at least one query path that exercises the new SQL surface, or explain why it could not be run.

Lesson from the skill market issue: the database was stamped at revision `9a8b7c6d5e4f`, but `skill_market_item` did not contain newly expected columns such as `market_kind`. The correct fix was a new forward migration (`a1b2c3d4e5f6`) that repairs missing columns, not resetting migration history or relying on the edited old migration.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
