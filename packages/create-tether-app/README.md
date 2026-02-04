# create-tether-app

CLI to scaffold [Tether](https://github.com/FabianUB/tether) AI/ML desktop applications.

## Usage

```bash
npx create-tether-app my-app
```

## Options

| Flag | Description |
|------|-------------|
| `--llm <provider>` | LLM backend: `ollama` (default), `local-llm`, `openai`, `custom` |
| `-y, --yes` | Skip prompts, use defaults |
| `--tailwind` | Include Tailwind CSS |
| `--skip-install` | Skip dependency installation |
| `--use-npm` | Use npm instead of pnpm |
| `--use-yarn` | Use yarn instead of pnpm |
| `-v, --verbose` | Show detailed output |
| `--check` | Verify required dependencies are installed |
| `--list-templates` | Show available LLM backends |
| `--dry-run` | Preview without creating files |

## Examples

```bash
# Interactive prompts
npx create-tether-app my-app

# Quick start with defaults
npx create-tether-app my-app -y

# With OpenAI backend
npx create-tether-app my-app --llm openai

# With Tailwind CSS
npx create-tether-app my-app --tailwind

# Check dependencies first
npx create-tether-app --check
```

## Requirements

- Node.js 18+
- pnpm 8+ (or npm/yarn)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Rust (cargo)

## Links

- [Documentation](https://github.com/FabianUB/tether)
- [Issues](https://github.com/FabianUB/tether/issues)
