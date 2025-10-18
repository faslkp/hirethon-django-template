# URL Shortener Frontend

React-based frontend for the URL Shortener application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file:
```bash
VITE_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Features

- User authentication (register/login)
- Organization management with role-based access control
- Namespace creation and management
- Short URL creation with custom codes
- Bulk URL upload via Excel
- QR code generation
- URL analytics (click tracking)

## Tech Stack

- React 18
- Vite
- React Router
- TanStack Query (React Query)
- Zustand (state management)
- Tailwind CSS
- Axios
