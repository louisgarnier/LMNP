# Technology Stack

This document outlines the technologies, frameworks, and tools used in this project.

## Frontend

### Framework
- **Nuxt 3** - Vue.js framework for building modern web applications
  - Version: 3.x
  - Features: Server-side rendering, static site generation, auto-imports

### Language & Tools
- **TypeScript** - Type-safe JavaScript
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Build tool and dev server (included with Nuxt 3)

### Styling
- **Tailwind CSS** - Utility-first CSS framework
- **CSS Modules** - Scoped CSS (if needed)

### Testing
- **Vitest** - Fast unit test framework (or Jest)
- **@vue/test-utils** - Vue component testing utilities

## Backend

### Framework
- **FastAPI** - Modern, fast web framework for building APIs with Python
  - Version: Latest
  - Features: Automatic API documentation, async support, type hints

### Language
- **Python 3.x** - Programming language
  - Recommended: Python 3.11+

### Database
- **SQLite** - Lightweight database (default, configurable)
  - Alternative options: PostgreSQL, MySQL
- **SQLAlchemy** - ORM for database operations (if needed)

### API Documentation
- **Swagger/OpenAPI** - Auto-generated API docs (built into FastAPI)

## Development Tools

### Version Control
- **Git** - Version control system
- **GitHub** - Repository hosting

### Package Management
- **npm/yarn/pnpm** - Frontend package manager
- **pip** - Python package manager

### Testing
- **Pytest** - Python testing framework (backend)
- **Vitest/Jest** - JavaScript testing framework (frontend)

### Code Quality
- **ESLint** - JavaScript/TypeScript linter
- **Prettier** - Code formatter (optional)
- **Black** - Python code formatter (optional)
- **Ruff** - Fast Python linter (optional)

## Development Environment

### IDE/Editor
- **Cursor** - AI-powered code editor
- **VS Code** - Alternative editor

### Environment Management
- **Virtual Environment** - Python virtual environment (venv)
- **Node Version Manager (nvm)** - Node.js version management (optional)

## Deployment (Future)

### Options
- **Vercel/Netlify** - Frontend deployment
- **Railway/Render/Fly.io** - Backend deployment
- **Docker** - Containerization (optional)
- **GitHub Actions** - CI/CD (optional)

## Configuration Files

### Frontend
- `nuxt.config.ts` - Nuxt configuration
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - Tailwind CSS configuration

### Backend
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration
- `.env` - Environment variables (not committed)

## Version Information

To check installed versions:

```bash
# Frontend
node --version
npm --version

# Backend
python3 --version
pip --version
```

## Notes

- Stack can be customized based on project needs
- Update this document when adding new technologies
- Keep versions updated for security and features

---

**Last Updated**: [Date when stack is finalized]

**Related Documents**:
- [Project Requirements](./requirements/README.md)
- [Setup Checklist](../../SETUP_CHECKLIST.md)

