---
title: Dress Tools AI Try-On
emoji: 👗
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# Dress Tools - AI Virtual Try-On API

Backend API for the AI virtual try-on application.

## Environment Variables

Set these in HF Spaces Settings → Secrets:
- `FASHN_API_KEY` - Your FASHN API key
- `TRYON_ENGINE` - Set to `fashn` for real AI, `mock` for testing
- `CORS_ORIGINS` - Frontend URL to allow (e.g., `https://dress-tools.vercel.app`)

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/images/upload` - Upload clothing/model images
- `POST /api/tryon/run` - Run virtual try-on
- `GET /docs` - API documentation
