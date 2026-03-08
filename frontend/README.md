# Frontend — Phishing Detection System

This directory is the home for the frontend application. HTML design mockups are already provided in `designs/` as a reference for the UI.

---

## Directory Structure

```
frontend/
├── README.md       # This file
└── designs/        # Static HTML design mockups (reference only)
    ├── dashboard.html
    ├── email.html
    ├── login.html
    └── security.html
```

---

## Getting Started

The backend exposes an **SMTP server** today and will expose a **REST API** for the frontend to consume. Before starting frontend development:

1. **Read the API docs** → [`../docs/BACKEND_API.md`](../docs/BACKEND_API.md)
2. **Review the design mockups** → open any `.html` file in `designs/` in your browser
3. **Spin up the backend** → see [`../backend/README.md`](../backend/README.md)

---

## Design Mockups

| File                    | Screen              |
|-------------------------|---------------------|
| `designs/login.html`    | Login / auth page   |
| `designs/dashboard.html`| Main dashboard      |
| `designs/email.html`    | Email detail view   |
| `designs/security.html` | Security settings   |

Open them directly in a browser — they are standalone HTML files with inline styles.

---

## Backend API Overview

The backend provides the following data your frontend will need:

| Resource             | Description                                          |
|----------------------|------------------------------------------------------|
| Users                | Register, authenticate, fetch profile                |
| Email Events         | List all emails scanned for a user                   |
| Predictions          | Risk level, phishing probability per email           |
| Trusted Domains      | Add / remove per-user trusted sender domains         |

See [`../docs/BACKEND_API.md`](../docs/BACKEND_API.md) for full request / response schemas.

---

## Suggested Tech Stack

Pick whatever fits the team — the backend is framework-agnostic. Common choices:

| Layer        | Options                                  |
|--------------|------------------------------------------|
| Framework    | React, Vue, Svelte, Next.js              |
| HTTP client  | Axios, Fetch API                          |
| Auth         | JWT (backend will provide tokens)        |
| Build tool   | Vite, Create React App                   |

Create your project inside this `frontend/` directory (e.g. `npm create vite@latest .`).

---

## Environment Variables

When the backend REST API is ready, you will need to configure the base URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

(Adjust the variable name to match your framework's convention.)
