# Scheduled Prompt Runner - Specification

## Project Overview

A Python-based system that schedules prompts to LLMs with web search capabilities and delivers responses via various channels. Uses GitHub Actions for zero-cost orchestration.

**Architecture Pattern**: Public code repo + Private data repo
- `prompt-runner` (public): The framework code
- User's private data repo: Prompts, personal configs, and persisted results

### Example Use Case: Daily Briefing

A personalized daily briefing that aggregates information based on your interests:
- News and updates relevant to your projects/interests
- Weather and calendar context
- Custom insights from topics you follow

---

## Technical Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | User requirement, excellent LLM SDK support |
| LLM | OpenAI Responses API with `web_search` tool | Strong reasoning models (o3, o4-mini), built-in web search |
| Scheduling | GitHub Actions | Free (unlimited for public repos, 2000 min/month private) |
| Email | Gmail SMTP + App Password | Zero cost, simple setup, no third-party services |
| Persistence | SQLite | Zero cost, portable, file-based, easy to version control |
| Config | YAML | Human-readable, easy to edit, supports complex nested structures |
| CLI | Click | Standard Python CLI framework, good UX |

### Key Design Principles

1. **Pluggable LLM Providers**: Abstract base class allows swapping OpenAI for Anthropic, Google, or local models
2. **Extensible Delivery**: Email first, but architecture supports Slack, Discord, webhooks, etc.
3. **Zero Infrastructure Cost**: Only pay for LLM API usage
4. **Separation of Concerns**: Public code repo + private data repo keeps personal configs secure

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (data repo)                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  1. Checkout data repo (private)                           │  │
│  │  2. Install prompt-runner from public repo                 │  │
│  │  3. Run prompt with config from data repo                  │  │
│  │  4. Commit results back to data repo                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     prompt-runner CLI                             │
│                                                                   │
│   ┌───────────┐    ┌───────────────────────────────────────┐     │
│   │  Config   │───→│          LLM Engine                   │     │
│   │  Loader   │    │  ┌─────────────────────────────────┐  │     │
│   └───────────┘    │  │ OpenAI Responses API            │  │     │
│        │           │  │ - o3/o4-mini (reasoning)        │  │     │
│        ▼           │  │ - web_search tool enabled       │  │     │
│   ┌───────────┐    │  └─────────────────────────────────┘  │     │
│   │  Prompt   │───→│                                       │     │
│   │  Builder  │    └───────────────────────────────────────┘     │
│   └───────────┘                     │                             │
│        │                            ▼                             │
│        │           ┌───────────────────────────────────────┐     │
│        │           │           Delivery                     │     │
│        │           │  - Email (Gmail SMTP)                  │     │
│        │           │  - Future: Slack, Discord, webhooks    │     │
│        │           └───────────────────────────────────────┘     │
│        │                            │                             │
│        ▼                            ▼                             │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                    Persistence                           │    │
│   │  - Run history (timestamp, prompt, response)             │    │
│   │  - Deduplication cache                                   │    │
│   │  - Response archive for reference                        │    │
│   └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Public Repo: `prompt-runner/`

```
prompt-runner/
├── .github/
│   └── workflows/
│       └── tests.yml               # CI for the framework
│
├── src/
│   └── prompt_runner/
│       ├── __init__.py
│       ├── __main__.py             # python -m prompt_runner
│       ├── cli.py                  # CLI entry point (click)
│       ├── runner.py               # Main orchestration logic
│       ├── config.py               # YAML config loading
│       │
│       ├── llm/                    # LLM provider abstraction
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract base class
│       │   ├── openai_provider.py  # OpenAI Responses API + web_search
│       │   └── registry.py         # Provider registration
│       │
│       ├── delivery/               # Response delivery channels
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract base class
│       │   └── email.py            # Gmail SMTP implementation
│       │
│       └── persistence/            # Data storage
│           ├── __init__.py
│           ├── base.py             # Abstract store interface
│           └── sqlite_store.py     # SQLite implementation
│
├── tests/
│   ├── __init__.py
│   ├── test_runner.py
│   ├── test_llm.py
│   └── test_delivery.py
│
├── examples/                       # Example configs (non-personal)
│   ├── prompts/
│   │   └── daily-briefing.yml
│   └── profiles/
│       └── example-profile.yml
│
├── pyproject.toml
├── SPEC.md
├── README.md
└── .env.example
```

### User's Private Data Repo (Example Structure)

```
my-prompt-data/
├── .github/
│   └── workflows/
│       └── daily-briefing.yml      # Scheduled workflow
│
├── prompts/
│   └── my-briefing.yml             # Personal prompt config
│
├── profiles/
│   └── me.yml                      # Personal preferences
│
├── data/
│   └── prompt_runner.db            # SQLite database
│
└── .gitignore
```

---

## Implementation Phases

### Phase 1: Core Framework
- [x] Initialize Python project with pyproject.toml
- [x] Implement LLM abstraction layer (`llm/base.py`)
- [x] Implement OpenAI provider with web_search support (`llm/openai_provider.py`)
- [x] Implement Gmail SMTP delivery (`delivery/email.py`)
- [x] Build CLI with `run` command (`cli.py`)
- [x] Add YAML config loading with Jinja2 templating (`config.py`)
- [ ] Add example configs (`examples/`)

### Phase 2: Testing & Documentation
- [ ] Unit tests for core components
- [ ] Integration test with mocked LLM
- [ ] README with setup instructions
- [ ] Example workflow for GitHub Actions

### Phase 3: Persistence Layer
- [ ] Implement SQLite store abstraction (`persistence/base.py`)
- [ ] Implement SQLite store (`persistence/sqlite_store.py`)
- [ ] Add run history tracking
- [ ] Add deduplication support

### Phase 4: Enhancements (Future)
- [ ] Additional LLM providers (Anthropic, Google)
- [ ] Additional delivery channels (Slack, Discord)
- [ ] Context fetchers (API calls, web scraping before prompting)
- [ ] Web UI for viewing history

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `GMAIL_SENDER` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail App Password (16 characters) |

---

## CLI Interface

```bash
# Run a prompt
prompt-runner run <prompt-name> --profile <profile.yml>

# List available prompts
prompt-runner list

# Validate configuration
prompt-runner validate <prompt-name> --profile <profile.yml>

# Run with dry-run (no LLM call, no delivery)
prompt-runner run <prompt-name> --profile <profile.yml> --dry-run
```

---

## Cost Estimate

| Item | Cost |
|------|------|
| GitHub Actions | Free (public repo) |
| OpenAI API | ~$0.10-0.50 per run |
| Gmail SMTP | Free |

**Monthly estimate for daily runs**: ~$3-15/month
