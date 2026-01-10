# Vulnerable Banana Sensei

> Transform your dependency vulnerabilities into educational comics

Vulnerable Banana Sensei is an AI-powered tool that scans your package.json for security vulnerabilities and generates custom comic strips that explain each issue in an engaging, memorable way. Built with Gemini 3 Pro for intelligent research and image generation.

## Features

- **Dependency Scanning** - Upload your package.json and scan against the OSV (Open Source Vulnerabilities) database
- **Smart Research** - AI-powered analysis explains what happened, why you should care, and how to fix it
- **Historical Incidents** - Researches past security incidents for packages without current vulnerabilities (left-pad, event-stream, colors, etc.)
- **Comic Generation** - Transforms security findings into custom illustrated comic strips using Gemini's image generation
- **Multiple Story Types** - Active threats (red), historical incidents (purple), and educational wisdom tales (blue)
- **Shareable Comics** - Each generated comic gets a unique URL for sharing with your team

## How It Works

1. **Upload** your package.json file
2. **Review** the story cards showing vulnerabilities and historical incidents
3. **Select** a story to illustrate
4. **Wait** 2-5 minutes while the AI sensei crafts your comic
5. **Share** the generated comic with your team

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vite + React + TypeScript + Tailwind CSS |
| Backend | FastAPI + Pydantic |
| LLM (Text) | Gemini 3 Pro Preview |
| LLM (Images) | Gemini 3 Pro Image Preview |
| Vulnerability Data | OSV (Open Source Vulnerabilities) API |
| Storage | Local filesystem (dev) / GCS (prod) |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- A Google AI API key with access to Gemini 3 Pro

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vulnerable-banana-sensei.git
   cd vulnerable-banana-sensei
   ```

2. Create your environment file:
   ```bash
   cp .env.example .env
   ```

3. Add your Gemini API key to `.env`:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

4. Start the services:
   ```bash
   docker compose up
   ```

5. Open http://localhost:3000 in your browser

### Test It Out

Upload the included test file to see it in action:
```bash
# The frontend will accept this file via drag & drop
test-fixtures/vulnerable-package.json
```

Or test the API directly:
```bash
curl -X POST http://localhost:8000/api/scan \
  -F "file=@test-fixtures/vulnerable-package.json" | jq
```

## Project Structure

```
vulnerable-banana-sensei/
├── backend-engine/           # FastAPI backend
│   └── src/vulnerable_banana/
│       ├── api/              # API routes
│       ├── models/           # Pydantic models
│       ├── services/         # Business logic (scanner, researcher, comic generator)
│       └── storage/          # Storage abstraction (local/GCS)
├── frontend-ui/              # React frontend
│   └── src/
│       ├── components/       # React components
│       ├── lib/              # API client, utilities
│       └── types/            # TypeScript interfaces
├── test-fixtures/            # Sample package.json files
├── documentation/            # Project docs and session logs
└── docker-compose.yml        # Local development orchestration
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/scan` | Upload and scan a package.json file |
| POST | `/api/generate-comic` | Generate a comic from a story card |
| GET | `/api/comic/{hash}` | Retrieve a generated comic |

## Why "Vulnerable Banana Sensei"?

The name comes from **Nano Banana Pro** - a playful nickname for `gemini-3-pro-image-preview`, the model that generates the comic images. The sensei theme represents the wise teacher who transforms complex security concepts into digestible visual stories.

## Screenshots

*Coming soon*

## Acknowledgments

- Built for the Gemini Hackathon 2026
- Vulnerability data from [OSV](https://osv.dev/)
- Powered by [Google Gemini](https://deepmind.google/technologies/gemini/)

## License

MIT
