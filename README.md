# Agent Skills

AI agent skills that bridge the gap between your agent and real-world tools — email, finance, documents, presentations, YouTube transcripts, and more.

These skills are small, self-contained, and composable. Each one tells an agent exactly how to install, configure, and use a specific tool via the terminal. No magic, no abstraction — just clear, battle-tested instructions that work across Claude Code, Codex, GitHub Copilot, and other coding agents.

## Quickstart

Clone this repo and copy the skills you need into your agent's skills directory:

```bash
git clone https://github.com/Jansen611/Agent-Skills.git
```

Each skill lives in `skills/<name>/` — some include reusable scripts under `scripts/`. Copy the entire skill folder into your agent's skills directory and you're ready to go.

## Skills

| Skill | Description | When to Use |
|---|---|---|
| [**himalaya-email-rust**](skills/himalaya-email-rust/SKILL.md) | CLI email client. IMAP, SMTP, OAuth 2.0, JSON output. | Check inbox, send/reply to emails, search/filter emails from terminal |
| [**yahoo-finance-python**](skills/yahoo-finance-python/SKILL.md) | Stock quotes, historical prices, fundamentals via yfinance. | Get stock price, download market data, fetch company financials |
| [**markitdown-python**](skills/markitdown-python/SKILL.md) | Convert files to Markdown using Microsoft's MarkItDown. | Read PDF/Word/Excel/PPT, extract text from documents, transcribe audio |
| [**pptx**](skills/pptx/SKILL.md) | Create professional PowerPoint presentations with pptxgenjs. | Make a slide deck, generate .pptx files, create pitch decks |
| [**siri-shortcut-editing**](skills/siri-shortcut-editing/SKILL.md) | Edit macOS Siri Shortcuts programmatically — decode, modify, re-sign. | Edit .shortcut files, programmatically modify shortcuts, resign shortcuts |
| [**youtube-transcript**](skills/youtube-transcript/SKILL.md) | Download YouTube video transcripts via yt-dlp. | Get captions/subtitles, transcribe YouTube videos, extract video text |
| [**grill-me**](skills/grill-me/SKILL.md) | Grilling session to stress-test a plan or design with relentless questions until every branch is resolved. _Derived from [@mattpocock](https://github.com/mattpocock/skills)._ | Get grilled on a design, clarify a plan, resolve decision trees |
| [**handoff-conversation**](skills/handoff-conversation/SKILL.md) | Compact the current conversation into a handoff document for another agent to pick up. _Derived from [@mattpocock](https://github.com/mattpocock/skills)._ | Hand off work to another agent, summarize conversation for continuation |

## Why These Skills Exist

### #1: Agents Are Bad at Tool Setup

Agents will happily hallucinate CLI flags, invent non-existent pip packages, or install tools globally without asking. Even when they know the right tool, they fumble the environment setup — wrong venv, missing PATH, incompatible versions.

These skills encode the exact setup dance for each tool: check PATH → check venv → install only as last resort. No guesswork, no drift.

### #2: Every Tool Has Sharp Edges

yt-dlp has a priority order for subtitles (manual → auto-generated → Whisper). pptxgenjs needs `NODE_PATH` set in non-interactive shells. Himalaya's OAuth 2.0 requires specific Azure AD redirect URI platform type. Yahoo Finance needs date range handling and rate limiting awareness.

These are lessons learned from real usage. The skills capture them so your agent doesn't have to rediscover them every time.

### #3: Skills Should Be Composable, Not Monolithic

Each skill does one thing. Want email + finance? Grab those two. Want document conversion + presentations? Grab those. You don't need to adopt a framework or change your workflow — just add the skills you need.

## Design

- **SKILL.md format** — Compatible with Claude Code custom commands, Codex skills, and GitHub Copilot agent skills. YAML frontmatter declares name, description, and allowed tools.
- **Tool-first** — Every skill assumes the agent has access to a terminal (`Bash`). No HTTP APIs, no SDK wrappers, no abstractions that break.
- **Progressive disclosure** — Setup pre-checks come first, then common usage, then advanced/edge cases. Agents can bail out after finding what they need.
- **Cross-platform** — macOS and Linux are first-class. Windows paths are included where relevant (markitdown).

## Contributing

These skills are personal tools I maintain for my own workflow. If you find them useful, feel free to fork and adapt. PRs with improvements are welcome — especially if you've hit an edge case I haven't documented.

## License

MIT © 2026 Jansen Lin — see [LICENSE](LICENSE) for details.
