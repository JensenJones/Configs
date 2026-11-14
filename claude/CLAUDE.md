# Operating rules

This is a work machine. The code is the company's and it is confidential.

## Talking to me

- Be concise. Lead with the answer or the result, then only what I need to act on it.
- Explain clearly: plain sentences, define a term the first time, no jargon for its own sake.
- No em dashes anywhere. No filler ("it's worth noting", "let's dive in"), no bolded-label bullet lists, no closing summary that repeats what you just said.
- Say what you verified and what you did not. Never report done for something you have not run.

## Ask, don't guess

When a task has two reasonable readings and the answer is only in my head (naming, scope, which of two similar things I meant, a behaviour change nobody asked for), ask before writing code. If reading the repo answers it, read the repo instead.

## Fit the repo before writing

Read the neighbouring files first. Match their naming, error handling, layout, includes and test style, even where you would do it differently. The company's conventions and style guide override everything in this file and in CPP.md.

Use what is already there. Check for an existing helper, container, allocator or utility before writing one, and for an existing dependency before adding one. Never add a third-party dependency without asking.

## Code quality

Write the direct version: the shortest correct implementation a stranger can read in one pass, with no layer for a caller who does not exist.

- Pick the right data structure and algorithm up front.
- No work inside a loop that could happen once outside it.
- Handle errors where you can act on them. No catch that swallows and continues.
- Early return over nested conditionals. Delete dead code, do not comment it out.
- Keep a change to what was asked. Mention other problems you notice; do not fix them unasked.

## Comments

- Default to none. Good names beat explanation.
- Comment only what is not obvious from the code: a workaround for a real bug (with a link), a non-intuitive invariant, a chosen tradeoff, a measured reason for an odd-looking optimisation.
- One line, above the code. Follow the file's existing doc-comment pattern if it has one.
- No contextual comments. The code is a final state, not a changelog: never "removed the old X", "fixed the bug where Y", "changed per request".
- No section banners, no restating the line below.

## Verify, don't assert

Build it and run it: the tests, the binary, the benchmark. Reasoning that it should work is not verification. If something fails, say so and show the output.

## Safety

Mistakes must not reach shared code. Work freely inside the checkout, and commit when a piece of work is complete, but:

- Never force push, push to a protected branch (main, master, develop, release), delete a branch or tag, or rewrite published history.
- Never discard uncommitted work (`git reset --hard`, `git clean`, `git checkout -- .`, `git restore`, recursive `rm`).
- Never create, merge, close, edit, review or comment on a pull request, merge request or issue, by any route (CLI, API, MCP tool or browser). Reading them is fine.
- Never publish, deploy, or change infrastructure, CI configuration, credentials or anything outside this checkout.
- Never run `sudo`.

A hook blocks most of these. When something is blocked, or is on this list, stop and give me the exact command to run. Do not look for another way to do it.

## Confidentiality

Never send company code, identifiers, file paths, data, logs or internal names to an outside service: no pasting into web searches, issue trackers, pastebins or public repositories. Search the web only with generic terms.

@CPP.md
@RTK.md
