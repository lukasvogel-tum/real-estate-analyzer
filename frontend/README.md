# Frontend MVP

Next.js + TypeScript frontend for the Family Office Brain MVP.

## Local Run

1. Install dependencies:
   - `npm install`
2. Configure API endpoint:
   - copy `.env.example` to `.env.local`
   - set `NEXT_PUBLIC_API_BASE_URL` (default: `http://127.0.0.1:8000`)
3. Start development server:
   - `npm run dev`

## Pages

- `/projects`: upload + project list
- `/projects/[projectName]`: project details + project-scoped chat
- `/workspace`: `realestate_global` and `global` chat scopes
