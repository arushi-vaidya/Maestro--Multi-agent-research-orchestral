# Evidence Timeline UI Layout Reference

## Page Structure

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        PAGE HEADER & NAVIGATION                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Evidence Timeline                                        [New Query Button] ║
║  Track how scientific evidence evolves over time...                         ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                       FILTER BAR (TIME RANGE)                                ║
║  TIME RANGE: [6m] [1y] [2y] [5y] [All]              [42 events shown]      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐  ║
║  │   LEFT PANEL (1/3)      │  │  RIGHT PANEL (2/3) - TIMELINE            │  ║
║  │                         │  │                                          │  ║
║  │ ┌─────────────────────┐ │  │  │  ┌─────────────────────────────────┐ │  ║
║  │ │ CONFIDENCE SUMMARY  │ │  │  │  │ EVENT 1 (Newest)                │ │  ║
║  │ │      72             │ │  │  │  │ ─────────────────────────────── │ │  ║
║  │ │      ↗ +14 pts      │ │  │  │  │ Nov 2024 | SUPPORTS | HIGH | 85%│ │  ║
║  │ │                     │ │  │  │  │ Phase 3 trial showing 12%       │ │  ║
║  │ │ Distribution:       │ │  │  │  │ improvement in HbA1c            │ │  ║
║  │ │ [====●●●●===]       │ │  │  │  │                                 │ │  ║
║  │ │                     │ │  │  │  │ Source: ClinicalTrials.gov      │ │  ║
║  │ │ Supporting: 28      │ │  │  │  │ [Show more]                     │ │  ║
║  │ │ Suggesting: 12      │ │  │  │  └─────────────────────────────────┘ │  ║
║  │ │ Contradicts: 3      │ │  │  │                                       │  ║
║  │ │                     │ │  │  │  ┌─────────────────────────────────┐ │  ║
║  │ └─────────────────────┘ │  │  ●  │ EVENT 2                         │ │  ║
║  │                         │  │  │  │ ─────────────────────────────── │ │  ║
║  │ ┌─────────────────────┐ │  │  │  │ Oct 2024 | SUGGESTS | MEDIUM   │ │  ║
║  │ │ EVIDENCE BREAKDOWN  │ │  │  │  │ 72% | +5 pts                    │ │  ║
║  │ │                     │ │  │  │  │ Market analysis indicates...    │ │  ║
║  │ │ ● Supporting: 28    │ │  │  │  │                                 │ │  ║
║  │ │ ● Suggesting: 12    │ │  │  │  │ [Show more]                     │ │  ║
║  │ │ ● Contradicting: 3  │ │  │  │  └─────────────────────────────────┘ │  ║
║  │ │ ───────────────────  │ │  │  │                                       │  ║
║  │ │ Total: 43           │ │  │  │  ┌─────────────────────────────────┐ │  ║
║  │ │                     │ │  │  ●  │ EVENT 3                         │ │  ║
║  │ └─────────────────────┘ │  │  │  │ ─────────────────────────────── │ │  ║
║  │                         │  │  │  │ Sep 2024 | CONTRADICTS | LOW    │ │  ║
║  │ ┌─────────────────────┐ │  │  │  │ 45% | -8 pts                    │ │  ║
║  │ │ DATE RANGE          │ │  │  │  │ Post-market surveillance data..│ │  ║
║  │ │ From: May 2023      │ │  │  │  │                                 │ │  ║
║  │ │ To: Jan 2026        │ │  │  │  │ [Show more]                     │ │  ║
║  │ │                     │ │  │  │  └─────────────────────────────────┘ │  ║
║  │ └─────────────────────┘ │  │  │  │                                    │  ║
║  │                         │  │  │  │         [Continue scrolling...]    │  ║
║  │ ✓ All evidence source-  │  │  └──────────────────────────────────────┘  ║
║  │   linked and            │  │                                          ║  ║
║  │   timestamped.          │  │                                          ║  ║
║  │                         │  │                                          ║  ║
║  └─────────────────────────┘  │                                          ║  ║
║                                │                                          ║  ║
║  Sticky on scroll               └──────────────────────────────────────────┘  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Left Panel: Confidence Summary Card

### Layout

```
┌──────────────────────────────────────────┐
│  CONFIDENCE SCORE + DELTA                │
│  ════════════════════════════════════════│
│                                          │
│  72                           ↗ +14 pts  │
│  Confidence Score             (green)    │
│  as of Jan 2026                          │
│                                          │
├──────────────────────────────────────────┤
│  EVIDENCE DISTRIBUTION                   │
│  ════════════════════════════════════════│
│                                          │
│  [═══ GREEN ══][═ AMBER ═][RED]         │
│                                          │
│  Supporting: 28 • Suggesting: 12        │
│  Contradicting: 3                       │
│                                          │
├──────────────────────────────────────────┤
│  ROS SCORE (if available)               │
│  ════════════════════════════════════════│
│                                          │
│  75                Supporting: 28        │
│  High               Contradicting: 3     │
│                                          │
├──────────────────────────────────────────┤
│  TREND                                   │
│  ════════════════════════════════════════│
│  Evidence is becoming STRONGER over time │
│  (+14 pts increase)                      │
│                                          │
├──────────────────────────────────────────┤
│  SUMMARY                                 │
│  Total Evidence Events: 43               │
│  Time Window: May 2023 → Jan 2026       │
│                                          │
└──────────────────────────────────────────┘
```

### Colors Used
- **Background**: #f5f9f6 (very light green)
- **Numbers**: #3A3634 (dark text)
- **Accent**: #6b8e6f (green for positive), #a89668 (red for negative)
- **Borders**: #E8E3DC (subtle gray)

---

## Right Panel: Evidence Timeline

### Individual Card Layout

```
┌────────────────────────────────────────────────────────┐
│ Header (polarity-tinted background)                    │
│ ────────────────────────────────────────────────────── │
│ Nov 2024 │ [SUPPORTS] [HIGH]    │    Confidence: 85%  │
│                                                        │
├────────────────────────────────────────────────────────┤
│ Body (white background)                                │
│                                                        │
│ Phase II Trial Results Published                      │
│                                                        │
│ Study demonstrated 12% improvement in HbA1c levels    │
│ in patients with type 2 diabetes over 24 weeks.       │
│                                                        │
│ ────────────────────────────────────────────────────── │
│ Source: ClinicalTrials.gov                            │
│ Agent: Clinical Trial                                 │
│ ID: NCT02149459                                       │
│                                                        │
├────────────────────────────────────────────────────────┤
│ Footer (light gray background)                         │
│                                                        │
│ NCT02149459               [Show more]                 │
│                                                        │
│ → On click "Show more", reveals:                      │
│   - View on ClinicalTrials.gov →                      │
│   - Recency weight: 0.92                              │
│   - Expanded metadata                                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Polarity Badge Styles

```
SUPPORTS:        SUGGESTS:         CONTRADICTS:
┌────────────┐  ┌────────────┐    ┌────────────┐
│ SUPPORTS   │  │ SUGGESTS   │    │CONTRADICTS │
│ bg: green  │  │ bg: amber  │    │ bg: red    │
│ text: white│  │ text: white│    │ text: white│
└────────────┘  └────────────┘    └────────────┘
```

### Quality Badge Styles

```
HIGH:            MEDIUM:          LOW:
┌────────────┐  ┌────────────┐  ┌────────────┐
│ HIGH       │  │ MEDIUM     │  │ LOW        │
│ bg: green  │  │ bg: amber  │  │ bg: gray   │
│ text: white│  │ text: white│  │ text: white│
└────────────┘  └────────────┘  └────────────┘
```

---

## Timeline Node Markers

Left spine with polarity-colored nodes:

```
    │
    ● ← GREEN (SUPPORTS)
    │
    │
    ● ← AMBER (SUGGESTS)
    │
    │
    ● ← RED (CONTRADICTS)
    │
```

---

## Color Reference

| Element | Color | Hex Code | Usage |
|---------|-------|----------|-------|
| Supporting | Green | #6b8e6f | SUPPORTS badge, node marker |
| Suggesting | Amber | #d4a574 | SUGGESTS badge, node marker |
| Contradicting | Red | #a89668 | CONTRADICTS badge, node marker |
| Background | Warm Cream | #FAFAF9 | Page background |
| Surface | White | #FFFFFF | Card backgrounds |
| Text | Dark Brown | #3A3634 | Primary text |
| Subtle | Taupe | #A8A39F | Secondary text |
| Border | Light Tan | #E8E3DC | Dividers |

---

## Interactive States

### Time Range Buttons

```
[6m]   [1y]   [2y]   [5y]   [All]

Selected:
[1y] ← background: #3A3634, text: white

Unselected:
[6m] ← background: transparent, text: #A8A39F
```

### Evidence Card Hover

```
Before:   shadow-sm (subtle)
Hover:    shadow-md (slightly more prominent)
Expanded: gray border-top appears above footer
```

---

## Responsive Considerations

### Desktop (Primary)
- 3-column grid: 1/3 + 2/3 split
- Left panel sticky on scroll
- Full pagination visible

### Tablet/Mobile (Future)
- Could stack vertically
- Left panel moves to top
- Full-width cards

*(Currently optimized for desktop per requirements)*

---

## Animations

```
Card Expansion:    opacity: 0→1, max-height: 0→auto (200ms)
Button Hover:      color transition (smooth)
Node Markers:      border-color change on parent hover (200ms)
Page Load:         No stagger effect (instant appearance)
                   ∵ Clear is better than animated for data viz
```

---

## Accessibility Notes

- ✅ Semantic HTML (no div-spam)
- ✅ Color not sole differentiator (badges + text)
- ✅ Sufficient contrast ratios
- ✅ Keyboard navigable (tab, enter for expand)
- ✅ Focus states visible (on buttons)
- ✅ ARIA labels on interactive elements
- ✅ Screen reader friendly (semantic structure)

---

## Data Flow Diagram

```
┌─────────────────────────────┐
│ GET /api/evidence/timeline  │
│         ↓                   │
│ EvidenceTimelineResponse    │
│         ↓                   │
│  Filter by Time Range       │
│         ↓                   │
│  Sort Newest First          │
│         ↓                   │
│  Calculate Metrics          │
│  - Avg Confidence           │
│  - Delta                    │
│  - Polarity Stats           │
│         ↓                   │
│  Render Left + Right Panels │
│         ↓                   │
│  Left: ConfidenceSummary    │
│  Right: Timeline + Cards    │
└─────────────────────────────┘

Optional:
┌─────────────────┐
│ GET /ros/latest │
│       ↓         │
│ ROS Context     │
│ (enrichment)    │
└─────────────────┘
```

