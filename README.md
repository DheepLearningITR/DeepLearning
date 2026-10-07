# FanDesk

A multi-agent demo for interns: a supervisor agent routes IPL questions to **Stats Guru** (text-to-SQL over Cricsheet data) and movie questions to **Cinema Buff** (Wikipedia), or declines. The route board shows each request's path live, with tokens, cost and time per step.

- App, setup and run instructions: [`fandesk/README.md`](fandesk/README.md)
- Design spec: [`fandesk-design.md`](fandesk-design.md)
- Product and design system: [`PRODUCT.md`](PRODUCT.md), [`DESIGN.md`](DESIGN.md)

Quick start:

```bash
cd fandesk
cp .env.example .env   # add your OPENROUTER_API_KEY
docker compose up --build
```

Then open http://localhost:8090 (Phoenix traces at http://localhost:6006).
