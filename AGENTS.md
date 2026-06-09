# Sprint 2 — Delivered 2026-06-09

## Components Created
- `TeamRadarChart.tsx` — Recharts RadarChart (8 axes: Elo, Form, xG, xGA, Opponent, WC Exp, Squad, History)
- `SortableTable.tsx` — Generic sortable table with column sorting, sort indicators (ChevronUp/Down/ChevronsUpDown), responsive horizontal scroll

## Pages Updated
- **Dashboard** (`/`) — Added group selector + stage filter dropdowns with clear button; filters affect displayed predictions and group cards
- **Rankings** (`/rankings`) — IGF table and Power Ranking tables now use `SortableTable`; new "Radar View" tab lets users pick any team and see its IGF component radar
- **Knockout** (`/knockout`) — Stage probabilities table uses `SortableTable`; podium responsive fix
- **Simulations/[id]** (`/simulations/[id]`) — Results table uses `SortableTable`
- **Teams** (`/teams`) — Click any team card to show IGF Radar Profile; search input filters by name; IGF score bar per team

## Responsive Improvements
- All tables wrapped in `overflow-x-auto` (via SortableTable and self-closing div)
- Grid layouts use `sm:`, `md:`, `lg:` breakpoints consistently
- Filter bar in dashboard wraps on mobile (`flex-wrap`)
- Podium cards use `sm:grid-cols-3` instead of `md:grid-cols-3`
- Teams grid uses `sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`

## Build Result
- `next build` — 0 errors, 13 pages generated
- First Load JS shared: 87.1 kB
- All bundle sizes within expected ranges (97 kB – 217 kB per route)

## Key Techniques
- Client-side sorting via `useSort` logic in SortableTable (useMemo + useState)
- Client-side filtering in Dashboard (group + stage selectors)
- Radar chart uses `Recharts` already installed
- No new npm dependencies added
