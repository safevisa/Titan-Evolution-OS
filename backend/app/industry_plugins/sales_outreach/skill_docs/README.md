# Sales Outreach — Skill Documentation
# Titan Evolution OS Industry Plugin
# Version: 0.1.0 (stub)
# License: MIT

This directory contains skill documents (SOPs, checklists, guides) that the Sales Outreach plugin's agents reference during task execution.

## Skill Docs (Planned)

| Skill Doc | Agent Role | Status |
|-----------|-----------|--------|
| `lead_research_checklist.md` | Sales Researcher | Stub — to be created |
| `icp_scoring_guide.md` | Sales Researcher | Stub — to be created |
| `email_templates.md` | Outreach Writer | Stub — to be created |
| `linkedin_outreach_guide.md` | Outreach Writer | Stub — to be created |
| `compliance_checklist.md` | Outreach Writer | Stub — to be created |
| `quality_rubric.md` | Sales Manager | Stub — to be created |
| `escalation_policy.md` | Sales Manager | Stub — to be created |

## Skill Doc Format

Each skill doc is a Markdown file with frontmatter:

```yaml
---
skill_id: lead_research_checklist
version: 0.1.0
category: sales/research
agent_roles: [sales_researcher]
token_estimate: 800
---
# Lead Research Checklist
...
```

## Reference Patterns

The workflow and agent role definitions in this plugin are informed by open-source sales automation patterns observed in the ecosystem (see `docs/radar/2026-05-17-daily-radar.md` for sources). No third-party code is included — only abstracted workflow patterns and evaluation criteria.

## Integration Notes

- All write actions (email send, CRM write) are stubs pending Phase 2 of Context Sync (Gmail send) and CRM integration connectors.
- Human approval gates (`require_human_approval: true`) are enforced by default — this is a security requirement, not optional.
- Tenant must have `plan: business` or higher and an active CRM/Gmail OAuth connection.
