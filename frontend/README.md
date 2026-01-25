# Windx Frontend

Vue 3 + TypeScript + Vite frontend for the Windx Configurator System.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Language**: TypeScript
- **Build Tool**: Vite
- **Router**: Vue Router 4
- **State Management**: Pinia
- **HTTP Client**: Axios

## Project Setup

### Install Dependencies

```bash
bun install
```

### Development Server

```bash
bun run dev
```

The app will be available at `http://localhost:5173`

### Type-Check

```bash
bun run type-check
```

### Build for Production

```bash
bun run build
```

### Preview Production Build

```bash
bun run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── assets/          # Static assets (CSS, images)
│   ├── components/      # Reusable Vue components
│   ├── router/          # Vue Router configuration
│   ├── services/        # API services
│   ├── stores/          # Pinia stores
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   ├── views/           # Page components
│   ├── App.vue          # Root component
│   └── main.ts          # Application entry point
├── public/              # Public static files
├── index.html           # HTML entry point
├── vite.config.ts       # Vite configuration
└── tsconfig.json        # TypeScript configuration
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## API Integration

The Vite dev server is configured to proxy API requests to the FastAPI backend:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API calls to `/api/*` are automatically proxied to the backend

## Authentication

The app uses JWT token authentication:
- Tokens are stored in `localStorage`
- Axios interceptor automatically adds `Authorization` header
- Router guards protect authenticated routes

## Next Steps

1. Install dependencies: `bun install`
2. Copy environment file: `cp .env.example .env`
3. Start dev server: `bun run dev`
4. Start building components in `src/components/`
5. Add more views in `src/views/`
6. Create Pinia stores for state management in `src/stores/`
