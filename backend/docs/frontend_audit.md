# Frontend Architecture Audit — Sprint 10

## Current Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 14 App Router pages
│   │   ├── bracket/
│   │   ├── calibration/
│   │   ├── comparison/
│   │   ├── explorer/
│   │   ├── export/
│   │   ├── groups/
│   │   ├── knockout/
│   │   ├── matches/
│   │   ├── predictions/
│   │   ├── rankings/
│   │   ├── reports/
│   │   ├── scenarios/
│   │   ├── simulations/
│   │   ├── teams/
│   │   ├── layout.tsx
│   │   ├── page.tsx (Dashboard)
│   │   ├── globals.css
│   │   └── error.tsx
│   ├── components/
│   │   ├── ui/            # Base UI (card, badge, button, skeleton, table)
│   │   ├── BenchmarkChart.tsx
│   │   ├── Bracket.tsx
│   │   ├── CalibrationCurveChart.tsx
│   │   ├── ConfidenceGauge.tsx
│   │   ├── DistributionHistogram.tsx
│   │   ├── Footer.tsx
│   │   ├── GroupHeatmap.tsx
│   │   ├── Navbar.tsx
│   │   ├── ProbabilityBar.tsx
│   │   ├── ReliabilityDiagram.tsx
│   │   ├── ScorelineChart.tsx
│   │   ├── SortableTable.tsx
│   │   ├── StageProgressBar.tsx
│   │   └── TeamRadarChart.tsx
│   └── lib/
│       ├── api.ts         # API client + TypeScript types
│       └── utils.ts       # Formatting, colors, stage labels
├── tailwind.config.ts
└── package.json
```

## Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Components**: Radix UI (Select, Tabs, Slot)
- **Utilities**: CVA, clsx, tailwind-merge

## Design Analysis

### Strengths
- Clean separation: `lib/api.ts` centralizes all API calls with typed interfaces
- Reusable UI primitives: Card, Badge, Skeleton with variants
- Dark/light ready: CSS variables for theming (`--background`, `--foreground`)
- Tailwind utility classes used correctly with `clsx` + `twMerge`
- Responsive layouts with grid breakpoints
- Skeleton loading states for all pages
- Inter font from Google Fonts

### Weaknesses
- **No dark mode**: Only light theme defined
- **No consistent spacing system**: Pages use inline `space-y-*` inconsistently
- **No typography scale**: Only `<h1>`, `<h2>` with inline classes
- **Navbar is overloaded**: 15 items with no hierarchy or grouping
- **No page descriptions**: Most pages lack clear titles/subtitles
- **No data visualization on most pages**: Only dashboard has charts
- **Matches page shows raw team IDs instead of names**: `home_team_id.slice(0,8)` — broken
- **No error boundaries**: Only basic error.tsx
- **No monitoring/observability pages**: Missing entirely
- **No explainability page**: Missing entirely
- **No historical data page**: Missing entirely
- **API client lacks caching**: Every page re-fetches on mount

### Technical Debt
- `TeamRadarChart.tsx` — uses hardcoded radar dimensions
- `Bracket.tsx` — may not handle 48-team format properly
- No automated tests
- No Storybook or component documentation
- Inconsistent use of `"use client"` directive

## What to Keep
| Component | Reason |
|-----------|--------|
| `ui/card.tsx` | Well-designed, reusable |
| `ui/badge.tsx` | Variants work well |
| `ui/skeleton.tsx` | Good loading states |
| `ui/button.tsx` | Standard button component |
| `ui/table.tsx` | Sortable table primitive |
| `lib/api.ts` | Complete typed API client — keep and extend |
| `lib/utils.ts` | All formatters, color functions — keep |
| `ProbabilityBar.tsx` | Core visual component |
| `globals.css` | CSS variables, container classes, stat classes |
| `Footer.tsx` | Simple, works |
| `TeamRadarChart.tsx` | Radar chart for team comparison |
| `ConfidenceGauge.tsx` | Gauge visualization |

## What to Replace
| Component | Reason |
|-----------|--------|
| `Navbar.tsx` | Overloaded, needs hierarchy + grouping |
| `layout.tsx` | Needs new font, dark mode, meta tags |
| `page.tsx` (Dashboard) | Needs redesign as Command Center |

## What to Rebuild
| Page | Reason |
|------|--------|
| `/teams/page.tsx` | Missing team detail page (`[id]`) |
| `/matches/page.tsx` | Shows raw IDs instead of names |
| `/comparison/page.tsx` | Not reviewed, likely basic |
| `/scenarios/page.tsx` | Not reviewed, likely basic |
| `/explorer/page.tsx` | Not reviewed |

## What to Create New
| Page | Reason |
|------|--------|
| `/overview` | Tournament overview with champion probs |
| `/teams/[id]` | Team Intelligence Center |
| `/compare` | Team Comparison Center (new route) |
| `/explainability` | Explainability Command Center |
| `/monitoring` | Monitoring Center |
| `/history` | Historical Evolution |
| `/bracket` | Tournament Bracket Center |

## Action Plan
1. Create `design-system/` with typography, spacing, colors
2. Rebuild `layout.tsx` with new Nav, dark mode
3. Create `/overview` — Tournament Overview
4. Create `/teams/[id]` — Team Intelligence
5. Create `/compare` — Team Comparison
6. Create `/matches` — Match Explorer (rebuild)
7. Create `/scenarios` — Scenario Lab (rebuild)
8. Create `/explainability` — Explainability Center
9. Create `/monitoring` — Monitoring Center
10. Create `/history` — Historical Evolution
11. Create `/bracket` — Bracket Center
12. Update `lib/api.ts` with new endpoints
13. Performance optimization
