# Vulnerable Banana - Claude Code Guidelines

## After Context Loss / Auto-Compact

**CRITICAL:** After any context loss, ALWAYS read these files in order before doing any work:

1. `documentation/sessions/` - Read the latest session file (highest number)
2. `documentation/implementation-tracker.md` - Current progress and next steps
3. `documentation/project-plans/*.md` - All 11 planning documents (full context)

## Project Overview

Vulnerable Banana transforms package dependency security reports into engaging, educational comics. Users upload a dependency file, get story options, and generate shareable comics about security incidents.

**Tech Stack:**
- Frontend: Vite + React + Tailwind (GitHub Pages)
- Backend: FastAPI + Pydantic AI (stateless, containerized)
- LLM: Gemini 3 Pro (text), Gemini 3 Pro Image Preview (comics)
- Storage: GCP Cloud Storage

## Implementation Philosophy

### Code Quality Standards

- **Elegant and robust code** - Clean, readable, well-structured
- **Full implementation** - Complete the feature properly, don't leave stubs
- **No shortcuts** - Do it right the first time
- **No backwards compatibility hacks** - We're building fresh, no legacy concerns
- **No unnecessary abstractions** - Keep it simple until complexity is needed
- **Type everything** - Full type hints in Python, TypeScript types for all interfaces

### What NOT To Do

- Don't add placeholder/stub implementations - implement fully or not at all
- Don't add TODO comments for "later" - either do it now or explicitly defer to Phase 2/3
- Don't over-engineer for hypothetical futures - build for current requirements
- Don't add unused code "just in case"
- Don't use cheap/fast models for quality-sensitive tasks - we chose Gemini 3 Pro deliberately

### Error Handling

- Handle errors gracefully with clear messages
- Use structured error responses (see 04-api-spec.md)
- Log errors with context for debugging
- Don't swallow exceptions silently

## Key Technical Decisions

These are **final decisions** - don't second-guess them during implementation:

| Decision | Choice | Doc Reference |
|----------|--------|---------------|
| Backend state | Stateless (no sessions) | 03-architecture.md, 04-api-spec.md |
| Image consistency | Chat Mode | 06-comic-generation.md |
| Research approach | Two-tier (quick scan, deep report) | 07-llm-integration.md |
| Text model | Gemini 3 Pro for ALL text tasks | 07-llm-integration.md |
| Image model | gemini-3-pro-image-preview | 07-llm-integration.md |
| Resolution | 1K (1376×768) | 06-comic-generation.md |
| API naming | snake_case Python → camelCase JSON | 10-code-conventions.md |

## Before Starting Any Task

1. Check `implementation-tracker.md` for current phase and next task
2. Read the relevant project-plans doc for that task
3. Update the tracker when starting a task (mark in_progress)
4. Update the tracker when completing a task (mark done)

## Before Auto-Compact

If you sense context is getting long, proactively:
1. Update `implementation-tracker.md` with current status
2. Create/update session file in `documentation/sessions/` with:
   - What was accomplished
   - Current state of implementation
   - Any decisions made
   - Next steps

## Package Management

- Python: **Always use `uv`** - never pip directly
- Node: Use npm

```bash
# Python
uv sync              # Install deps
uv run pytest        # Run tests
uv add <package>     # Add dependency

# Node
npm install
npm run dev
```

## File Structure Reference

```
vulnerable-banana/
├── CLAUDE.md                    # This file
├── docker-compose.yml           # Local dev orchestration
├── .env                         # Environment variables (not committed)
├── .env.example                 # Environment template
│
├── backend-engine/              # Python FastAPI backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/vulnerable_banana/
│       ├── main.py              # FastAPI app
│       ├── config.py            # Settings
│       ├── api/routes.py        # Endpoints
│       ├── services/            # Business logic
│       ├── models/              # Pydantic models
│       └── storage/             # GCS/local storage
│
├── frontend-ui/                 # React frontend
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── components/          # React components
│       ├── lib/                 # Utilities (api.ts, storage.ts)
│       └── types/               # TypeScript interfaces
│
├── data/                        # Local storage (dev only, gitignored)
│
└── documentation/
    ├── implementation-tracker.md
    ├── sessions/
    └── project-plans/
```

## Quick Reference Links

- API Spec: `documentation/project-plans/04-api-spec.md`
- Data Models: `documentation/project-plans/05-data-models.md`
- Comic Generation: `documentation/project-plans/06-comic-generation.md`
- LLM Integration: `documentation/project-plans/07-llm-integration.md`
- Implementation Phases: `documentation/project-plans/08-implementation-phases.md`
- Code Conventions: `documentation/project-plans/10-code-conventions.md`
- Local Development: `documentation/project-plans/11-local-development.md`

## Debugging

View backend logs:
```bash
docker compose logs -f backend
```

Filter for errors:
```bash
docker compose logs backend | grep '"level":"error"'
```

See `11-local-development.md` for full logging strategy and debugging guide.
