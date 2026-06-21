# Design System — ForecastEngine2026 Command Center

## Typography
- Headings: Inter (Google Fonts), weights 600/700
- Body: Inter, weight 400/500
- Data/Metrics: JetBrains Mono (monospace), weight 400/500
- Scale: text-xs (0.75rem), text-sm (0.875rem), text-base (1rem), text-lg (1.125rem), text-xl (1.25rem), text-2xl (1.5rem), text-3xl (1.875rem)

## Colors

### Light Mode
| Token | Hex | Usage |
|-------|-----|-------|
| --background | #f8fafc | Page background |
| --foreground | #0f172a | Body text |
| --surface | #ffffff | Cards, panels |
| --border | #e2e8f0 | Borders, dividers |
| --muted | #94a3b8 | Secondary text |

### Dark Mode
| Token | Hex | Usage |
|-------|-----|-------|
| --background | #0a0f1a | Page background |
| --foreground | #f1f5f9 | Body text |
| --surface | #0f172a | Cards, panels |
| --border | #1e293b | Borders, dividers |
| --muted | #94a3b8 | Secondary text |

### Accent
- Primary: Blue (#3b82f6 → #2563eb)
- Positive: Green (#22c55e)
- Warning: Yellow (#eab308)
- Negative: Red (#ef4444)
- Info: Blue (#3b82f6)

## Spacing
- 4px increments: 1, 2, 3, 4, 5, 6, 8, 10, 12, 16
- Container padding: px-4 (mobile), sm:px-6, lg:px-8
- Section gap: space-y-6 or space-y-8
- Card padding: p-5

## Components

### Panel
- Container: rounded-xl, border, shadow-sm
- Header: border-bottom, flex row, px-5 py-4
- Body: p-5
- Title: uppercase, tracking-wider, text-xs, font-semibold

### Card
- Same as existing: rounded-xl, border, shadow-sm, p-6
- Header: p-6 pb-2
- Content: p-6 pt-0

### Metric Badge
- Background + text color for status: ok/green, warn/yellow, fail/red
- Font: monospace, small
- Rounded-md, px-2 py-0.5

### Grids
- dashboard: 1/2/3/4 columns (mobile/desktop)
- panels: 1/2 columns

## Charts
- Library: Recharts
- Line color: primary-500
- Bar fill: primary-500
- Area fill: primary-100/primary-500 gradient
- Grid: #e2e8f0
- Tooltip: white surface with shadow
- Legend: bottom, text-sm

## Loading States
- Skeleton: animate-pulse, rounded-md, bg-gray-200
- Page skeleton: 3 skeleton cards + header
- Table skeleton: header row + 6 data rows
