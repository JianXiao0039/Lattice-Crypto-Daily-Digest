# Phase 14D Cross-Operator Route Prompt Safety Review

Status: `codex_deepseek_kimi_prompt_safety_ready`.

Route prompt safety checks:

- active project path defined;
- private PhD / ResearchArtifacts / ResearchOS paths forbidden;
- git add/commit/push/tag forbidden unless explicitly authorized in a separate phase;
- background automation forbidden;
- source/ranking/taxonomy changes forbidden unless phase explicitly allows;
- external LLM runtime forbidden;
- manual annotation workflows forbidden;
- source-health caveats required;
- final report required;
- Codex review required for code changes;
- DeepSeek-Claude and Kimi Code are fallback runners, not release owners.
