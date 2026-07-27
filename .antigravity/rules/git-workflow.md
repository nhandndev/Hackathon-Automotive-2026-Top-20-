---
description: "User Preferences for Git Workflow and Branching"
---

# Git Workflow & Commit Rules

Always adhere to the following guardrails when handling Git operations:

1. **Never Automate Commits**: NEVER execute `git commit` commands on behalf of the user. The user prefers to review and execute commits manually.
2. **Branch & Commit Prefixes**: When providing Git instructions, generating branch names, or suggesting commit messages, strictly use the following prefixes:
   - `refactor/`
   - `migration/`
   - `feat/`
3. **Instruction Format**: If the user asks how to commit or branch, provide the exact commands for them to copy and run, using the prefixes above. Do NOT run the commands for them.
