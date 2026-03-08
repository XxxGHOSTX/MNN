# MNN Ops Frontend

React + Vite dashboard for MNN operator authentication and observability.

## Local run

```bash
yarn install
yarn dev
```

Optional backend URL configuration:

```bash
cp .env.example .env
```

## Production build

```bash
yarn build
yarn preview
```

## Required backend endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET /dashboard/overview`
- `POST /query`
