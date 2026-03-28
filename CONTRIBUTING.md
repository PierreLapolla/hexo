# Contributing to Hexo

Thanks for contributing.

## Before You Start

- Read [RULES.md](RULES.md) to align with game behavior expectations.
- Check existing issues and pull requests before opening new ones.

## Reporting Issues

When opening an issue, include:

- clear title and concise summary
- expected behavior vs actual behavior
- minimal reproduction steps
- environment details (OS, Python version, command used)
- logs or traceback when relevant

Use one issue per distinct bug or feature request.

## Proposing Features

- Describe the use case first, then the proposed API.
- Call out rule or compatibility impacts.
- Prefer incremental changes over large all-in-one proposals.

## Pull Request Guidelines

- Keep PRs focused and scoped to one change area.
- Link the related issue (for example: `Closes #12`).
- Add or update tests for behavior changes.
- Update documentation when public API or behavior changes.
- Ensure linting and tests pass locally before requesting review.

## Development Setup

```bash
uv sync
uv run pre-commit install
```

## Local Quality Checks

```bash
uv run pytest
uvx ruff check . --fix
uvx ruff format .
```

## Commit Guidance

- Use clear commit messages in imperative form.
- Explain why a change was made when not obvious from the diff.

## Code Review Expectations

- Be respectful and technical in review discussions.
- Address feedback with follow-up commits.
- If you disagree with feedback, document tradeoffs and rationale clearly.
