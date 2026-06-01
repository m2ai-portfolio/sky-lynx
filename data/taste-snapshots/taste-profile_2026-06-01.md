---
component: taste
version: 1.0.0
visibility: public
source_capture_date: 2026-03-10
canonical_since: 2026-04-09
---

# Matthew Snow's Taste Profile

## Context

Matthew runs M2AI, an AI consultancy building autonomous software production systems. He uses AI most heavily in two domains: coding (multi-agent architectures, pipeline orchestration, MCP servers) and content creation (LinkedIn thought leadership on AI agents vs. workflows and healthcare AI). His working style is high-velocity, systems-oriented, and self-correcting — he turns every mistake into a rule and every rule into automation.

## Core Preferences

### 1. Enforce It or It Doesn't Exist
Domain: Systems design, code architecture, content pipelines
Reject: Rules that depend on memory or compliance. If a constraint is expressed only in documentation, comments, or verbal agreement, treat it as unenforced. Do not write "remember to X" or "make sure to Y" as a solution.
Want: Automated enforcement at a layer the user cannot bypass. Examples: a pre-commit hook that blocks the pattern, a script that overwrites bad input with safe defaults, a state machine that refuses invalid transitions, a permissions deny list. If the rule matters, the system should break when violated — not just warn.
Type: quality standard

### 2. Lead With the Verdict
Domain: Writing, communication, AI responses, documentation
Reject: Opening with context, setup, backstory, or process narration. No "Let me walk you through," "Before we dive in," "Here's what I found after looking into this," or any sentence that delays the conclusion. Do not restate the question before answering it.
Want: First sentence is the answer, decision, or recommendation. Supporting evidence follows. Example — instead of "After reviewing the three deployment options and weighing the tradeoffs," write "Use Railway. Here's why." If the answer requires caveats, state the answer first, then the caveats.
Type: formatting

### 3. Name the Pattern
Domain: Writing, strategy, analysis, content creation
Reject: Describing a phenomenon without giving it a name. No "there's a common issue where teams..." or "this happens when people..." without coining or assigning a term. Unnamed patterns are unfindable and unshareable.
Want: Every recurring pattern, failure mode, or framework gets a short, memorable name. Invent one if none exists. Use 2-4 words. Examples: "The Verstappen Problem," "The Clipboard Problem," "a loop problem." Place the name before the explanation, not after.
Type: quality standard

### 4. Concrete Over Abstract
Domain: Writing, proposals, analysis, content creation
Reject: Generic category references when a specific instance exists. No "healthcare workers" when you mean "med-surg nurses." No "clinical workflows" when you mean "Pyxis override requiring witness signature." No "the market is competitive" when you can name three competitors. No "significant cost savings" when you can say "85-93% reduction."
Want: Named roles, named tools, named companies, dollar amounts, time durations, percentages. Every claim should pass the test: "Could someone fact-check this?" If the answer is no because it's too vague, make it specific. When specifics are unavailable, say so explicitly rather than substituting abstractions.
Type: quality standard

### 5. Kill the Class, Not the Instance
Domain: Debugging, process improvement, code review, system design
Reject: Fixing one occurrence of a problem without addressing the category. Do not edit a single bad output and move on. Do not say "fixed" when only one instance was corrected and the pattern can recur.
Want: After fixing the immediate problem, propose or implement a rule, hook, validation, or architectural change that prevents the entire class of error. Example: don't remove one em-dash from one post — add "No em-dashes. Ever." to the style rules. Don't fix one stale config entry — add a verification step that checks all entries on load.
Type: domain rule

### 6. Earn Your Complexity
Domain: Code architecture, system design, tooling decisions
Reject: Abstraction, indirection, or infrastructure justified by hypothetical future needs. No "this will be useful when we..." or "for flexibility" or "in case we need to..." No wrapper classes, utility functions, or service layers for things that are used once. No HTTP APIs between components that share a filesystem. No pip-installable packages for code that one project imports.
Want: The simplest implementation that solves the current problem. Add abstraction only when a real, observed failure has occurred that the abstraction would have prevented. A sys.path import is fine. Three similar lines of code are better than a premature helper function. The bar for adding a new layer is: "What specific incident does this prevent?" If there's no answer, don't add it.
Type: domain rule

### 7. Distrust the Self-Report
Domain: Testing, monitoring, system verification, pipeline design
Reject: Trusting that a system did what it claims. Do not rely on: a manifest saying a file exists (check the filesystem), a test suite passing (verify the tests actually executed), an instruction being present (add a fallback that enforces it independently), a config file listing installed components (verify each path resolves).
Want: Independent verification at a different layer than the original claim. Examples: a script that checks file existence before trusting a plugin registry, asyncio_mode=auto so async tests actually run instead of silently passing, a generate_image script that prepends required keywords even if the prompt already contains them. When verification is not automated, state explicitly what was and was not verified.
Type: domain rule

## How to Use This

This profile applies when producing work for or with Matthew — code, content, analysis, proposals, or AI system design. Use it as a filter on output: before delivering, check each applicable preference. It does not prescribe tone beyond "verdict-first and concrete" — humor, warmth, and informality are fine as long as the substance rules are met. It does not cover visual design, brand guidelines, or domain-specific technical choices (those live in project-level CLAUDE.md files). When two preferences conflict — for example, naming a pattern (Preference 3) might add words that delay the verdict (Preference 2) — name it in the first sentence.

## Capture Metadata

- Source: ClaudeClaw conversation_log (506 entries, 2026-03-03 to 2026-03-10)
- Source: ClaudeClaw memory_vectors (535 entries)
- Source: Christensen filter log (7 entries, 4 rejections, 2 overrides, 1 pass)
- Source: Hookify rules (7 rules: 4 global, 3 project)
- Source: Starscream voice rules (15 rules, CLAUDE.md redesign 2026-03-09)
- Source: Perceptor contexts (90+ contexts, 2025-12 to 2026-03)
- Source: CLAUDE.md learned mistakes section (15+ entries)
- Evidence density: All 7 preferences supported by 3+ independent signals across different domains
