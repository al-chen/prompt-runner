# Prompt Runner

Schedule prompts to LLMs with web search capabilities and deliver responses via email.

## Installation

```bash
pip install -e .
```

## Quick Start

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

2. (Optional) Set Gmail credentials for email delivery:
   ```bash
   export GMAIL_SENDER=your.email@gmail.com
   export GMAIL_APP_PASSWORD=xxxxxxxxxxxx  # 16-character App Password
   ```

   To generate an App Password:
   - Enable 2FA on your Google Account
   - Go to Google Account → Security → App passwords
   - Generate a new app password for "Mail"

3. Run a sample prompt:
   ```bash
   prompt-runner run examples/prompts/daily-briefing.yml --profile examples/profiles/example-profile.yml --no-deliver
   ```

This runs the example daily briefing prompt and prints the LLM response to stdout.

## Usage

```bash
# Run a prompt (looks in prompts/ directory)
prompt-runner run <prompt-name>

# Run with a specific file path
prompt-runner run ./path/to/prompt.yml

# Dry run (validate config, no API call)
prompt-runner run <prompt-name> --dry-run

# Skip email delivery
prompt-runner run <prompt-name> --no-deliver

# Save response to file
prompt-runner run <prompt-name> --output response.txt

# List available prompts
prompt-runner list

# Validate a prompt config
prompt-runner validate <prompt-name>

# Run with a profile for personalization
prompt-runner run <prompt-name> --profile examples/profiles/example-profile.yml
```

## Templating

Prompt configs support Jinja2 templating for dynamic content. Use `{{ variable }}` syntax in your YAML files.

### Built-in Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `current_date` | Today's date | `2024-01-15` |
| `current_time` | Current time (HH:MM) | `14:30` |
| `current_datetime` | ISO 8601 datetime | `2024-01-15T14:30:00` |
| `current_weekday` | Day of the week | `Monday` |
| `env` | Environment variables | `{{ env.HOME }}` |

### Profiles

Profiles are YAML files containing personal data for template substitution. Pass them with `--profile`:

```bash
prompt-runner run examples/prompts/daily-briefing.yml --profile examples/profiles/example-profile.yml
```

**Profile structure** (`examples/profiles/example-profile.yml`):
```yaml
name: Jane
location: New York
email: jane@example.com
interests:
  - technology
  - cooking
  - travel
```

Profile variables are available in two ways:
- Directly by name: `{{ name }}`, `{{ location }}`
- Under `profile`: `{{ profile.name }}`, `{{ profile.interests }}`

### Example Prompt with Templating

**Prompt** (`examples/prompts/daily-briefing.yml`):
```yaml
name: daily-briefing
prompt: |
  Good {{ current_weekday }}, {{ name }}!

  Give me a personalized briefing for someone in {{ location }}
  interested in: {{ interests | join(", ") }}.

  Today's date is {{ current_date }}.
llm:
  provider: openai
  model: gpt-4o
  enable_web_search: true
delivery:
  provider: email
  recipients:
    - {{ email }}
  subject: "Daily Briefing for {{ current_date }}"
```

**Run it:**
```bash
prompt-runner run examples/prompts/daily-briefing.yml --profile examples/profiles/example-profile.yml --dry-run
```
