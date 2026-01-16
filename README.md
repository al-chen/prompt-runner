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

2. Run a sample prompt:
   ```bash
   prompt-runner run test-prompt --no-deliver
   ```

This runs `prompts/test-prompt.yml` and prints the LLM response to stdout.

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
```
