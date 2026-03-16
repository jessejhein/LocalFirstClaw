# AGENTS.md - Project Constitution for LocalFirstClaw

## Core Development Principles

### Commit-First Development
- **Commit often after every significant work chunk** - commits are the primary tracking and history of this project
- Each commit should represent a logical unit of work (test, implementation, fix, etc.)
- Never accumulate uncommitted changes for long periods
- Use descriptive commit messages that explain the "why" not just the "what"
- Commit frequently enough that you can easily rollback to any working state

### Test-Driven Development (TDD) Workflow
Follow this precise cycle for all feature development:

1. **Setup Phase** (once): Initial configuration and test framework setup
2. **Write Tests First**: Create failing tests that define expected behavior
3. **Commit Tests**: Commit the test files before any implementation
4. **Write Code**: Implement only what's needed to make tests pass
5. **Commit Implementation**: Commit the working implementation
6. **Fix Anything**: Address any issues discovered during implementation
7. **Commit Fixes**: Commit fixes as separate logical units
8. **Repeat**: Continue this cycle for each feature or enhancement

### Testing Guidelines
- Run tests frequently during development (at least after every commit)
- Ensure all tests pass before committing code changes
- Write tests for edge cases and error conditions, not just happy paths
- Keep tests independent and focused on single behaviors
- Use descriptive test names that document expected behavior

### Code Quality Standards
- Follow Python script guidelines from `/home/openclaw/openclaw-tools/language-specs/python-script.md`
- Use flake8 and autopep8 for code quality (max 120 character lines)
- Maintain consistent logging with proper lazy evaluation
- Use dataclasses for complex return values (>3 items)
- Prefer clear, readable code over clever optimizations

## Project Rules

### Package Management
- This is a multi-package Python project
- Use pyproject.toml for all package configurations
- Keep dependencies minimal and well-justified
- Document all third-party dependencies in README files

### Architecture Adherence
- Follow the "spinal cord + hypothalamus" architecture from IDEA_MVP.md
- Keep components modular and loosely coupled
- Abstract LLM interactions behind the AgentInterface layer
- Maintain separation between gateway agents, journal, and tools

### Documentation Requirements
- All public functions must have proper docstrings
- Include type hints for function arguments and return values
- Update planning docs when architectural decisions change
- Document API endpoints with clear descriptions

### Error Handling
- All functions should raise appropriate exceptions
- Log all errors with proper context using child loggers
- Never use bare `except:` clauses - always specify exception types
- Return meaningful error messages for user-facing errors

## Workspace Conventions

### File Organization
- Use clear, descriptive filenames based on main class/function
- One class per file for better maintainability
- Keep related utility functions in the same file as the main class
- Use `__init__.py` to expose public module interfaces

### Git Workflow
- Feature branches for significant new features
- Direct commits for minor fixes and documentation
- Pull requests for major architectural changes
- Always verify tests pass before pushing

## Agent-Specific Guidelines

### When Writing Tests
- Think about edge cases first
- Consider both success and failure scenarios
- Use descriptive assertions that document expectations
- Mock external dependencies (LLM calls, file I/O, etc.)

### When Writing Code
- Write just enough to make tests pass
- Avoid speculative "future-proofing" code
- Keep functions small and focused (<50 lines ideally)
- Refactor when code becomes complex, but commit before refactoring

### When Reviewing Code
- Ensure all tests pass
- Check commit message clarity and granularity
- Verify no unnecessary dependencies were added
- Confirm logging follows lazy evaluation pattern

## Priority Guidelines

### High Priority (Do First)
- Core architecture and interfaces (AgentInterface, Gateway)
- Test framework setup and baseline tests
- Package structure and configuration
- Critical integrations (LiteLLM, FastAPI)

### Medium Priority (Do Second)
- Tool implementations
- Journal system
- Agent workspace structure
- Configuration management

### Lower Priority (Do Later)
- UI components (TUI, WebUI)
- Advanced scheduling features
- Performance optimizations
- Nice-to-have tool additions

## Success Metrics

### Project Health
- High commit frequency with meaningful messages
- Test coverage for all core functionality
- Clean git history without "fixup" commits
- Minimal technical debt accumulation

### Development Velocity
- Consistent progress toward MVP goals
- Features delivered through TDD cycle
- No breaking changes in working code
- Clear documentation of architectural decisions

## Reminders

- **COMMITS ARE YOUR HISTORY** - commit frequently and meaningfully
- **TESTS DRIVE DESIGN** - let tests guide your implementation
- **SIMPLICITY FIRST** - prefer dumb solutions over complex ones
- **EVERYTHING LOGGED** - make the journal the source of truth
- **HUMAN-EDITABLE CONFIG** - keep it YAML and markdown

This constitution guides all development on LocalFirstClaw. Follow it, commit often, and build incrementally through testing.
