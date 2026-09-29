---
name: pptx-rtl-hebrew
description: >
  Build Hebrew RTL PowerPoint presentations with pptxgenjs. Use this skill whenever the user
  asks to create a presentation, deck, or slides in Hebrew — even if they don't say "RTL"
  explicitly. Covers the core RTL layout rules: step boxes flow right-to-left (step 1 = rightmost),
  arrows point left (←), text aligns right, and all flow diagrams are mirrored vs. English.
  Also covers Hebrew-safe font choices, color palettes, and the full pptxgenjs helper
  functions for RTL step boxes, session cards, and title bars. Read this skill before writing
  any pptxgenjs code for Hebrew content.
---

# Hebrew RTL PowerPoint – pptxgenjs

## The Core Problem

pptxgenjs has no built-in RTL layout mode. Every coordinate is in inches from the
top-left corner, so the developer must manually mirror all horizontal layouts.

**English (LTR):** Step 1 → Step 2 → Step 3  (leftmost first)  
**Hebrew (RTL):**  שלב 3 ← שלב 2 ← שלב 1  (rightmost first, arrows point ←)

---

## Rule Summary

| Element | English default | Hebrew RTL |
|---|---|---|
| Step boxes | Left → Right | Right → Left (step 1 = max X) |
| Arrows between steps | → | ← |
| Text align | `"left"` | `"right"` + `rtlMode: true` |
| Column headers | Left first | Right first |
| Timeline | Left = start | Right = start |
| Legend items | Left = item 1 | Right = item 1 |

---

## Required text options (every Hebrew text element)

```javascript
s.addText("טקסט עברי", {
  x, y, w, h,
  fontFace: "Arial",   // Arial renders Hebrew correctly in pptx
  rtlMode: true,       // Critical – without this, bidi rendering breaks
  align: "right",      // Always "right" for Hebrew paragraphs
  // ... other options
});
```

**Never** use `reading_order` in pptxgenjs (that's an openpyxl parameter — it will throw).

---

## RTL box layout helper

Use this function to calculate x-positions for N equal-width boxes flowing right to left.
`positions[0]` is **step 1** (rightmost), `positions[N-1]` is step N (leftmost).

```javascript
function rtlBoxes(n, slideW = 10, margin = 0.3, boxW = null, gap = 0.45) {
  if (!boxW) {
    boxW = (slideW - 2 * margin - gap * (n - 1)) / n;
  }
  const positions = [];
  for (let i = 0; i < n; i++) {
    // i=0 → step 1 → rightmost
    const x = slideW - margin - boxW - i * (boxW + gap);
    positions.push({ x, w: boxW });
  }
  return positions;
}
```

### Worked examples

**4 boxes, 10″ slide, margin 0.3, gap 0.45:**
- Step 1: x ≈ 7.68  (rightmost)
- Step 2: x ≈ 5.23
- Step 3: x ≈ 2.78
- Step 4: x ≈ 0.33  (leftmost)

**3 boxes, 10″ slide, margin 0.3, gap 0.4:**
- Step 1: x ≈ 6.87  (rightmost)
- Step 2: x ≈ 3.67
- Step 3: x ≈ 0.47  (leftmost)

---

## drawRtlSteps() — numbered step boxes with arrows

Full helper for drawing a horizontal RTL step flow on a slide:

```javascript
function drawRtlSteps(s, pres, steps, opts = {}) {
  const {
    y = 1.2, h = 1.4,
    slideW = 10, margin = 0.3, gap = 0.38,
    numBg = "1E2761",    // circle behind step number
    boxBg = "F4F7FB",    // default box background
    arrowColor = "64748B"
  } = opts;

  const pos = rtlBoxes(steps.length, slideW, margin, null, gap);

  steps.forEach((step, i) => {
    const { x, w } = pos[i];

    // Box
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color: step.bg || boxBg },
      line: { color: step.border || "E2E8F0", width: 1.5 },
      shadow: { type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.15 }
    });

    // Number circle (top-right corner of box)
    const r = 0.32;
    s.addShape(pres.shapes.OVAL, {
      x: x + w - r - 0.1, y: y + 0.08, w: r * 2, h: r * 2,
      fill: { color: numBg }, line: { color: numBg }
    });
    s.addText(String(i + 1), {
      x: x + w - r - 0.1, y: y + 0.08, w: r * 2, h: r * 2,
      fontFace: "Arial", fontSize: 14, bold: true, color: "FFFFFF",
      align: "center", valign: "middle"
    });

    // Title (to the left of the circle)
    s.addText(step.title, {
      x: x + 0.1, y: y + 0.08, w: w - r * 2 - 0.25, h: 0.5,
      fontFace: "Arial", fontSize: 13, bold: true,
      color: step.titleColor || "1E2761",
      rtlMode: true, align: "right", valign: "middle"
    });

    // Body text
    if (step.body) {
      s.addText(step.body, {
        x: x + 0.1, y: y + 0.62, w: w - 0.2, h: h - 0.72,
        fontFace: "Arial", fontSize: 11,
        color: step.bodyColor || "64748B",
        rtlMode: true, align: "right", valign: "top"
      });
    }

    // Arrow ← between this box and the one to its left
    if (i < steps.length - 1) {
      const nextX = pos[i + 1].x + pos[i + 1].w;
      s.addText("←", {
        x: nextX + 0.04,
        y: y + h / 2 - 0.22,
        w: x - nextX - 0.08,
        h: 0.44,
        fontFace: "Arial", fontSize: 18, bold: true,
        color: arrowColor, align: "center", valign: "middle"
      });
    }
  });
}
```

### Usage

```javascript
drawRtlSteps(s, pres, [
  { title: "שלב ראשון",  body: "תיאור קצר",  bg: "E0F4F6", border: "028090" },
  { title: "שלב שני",   body: "תיאור קצר",  bg: "E0F4F6", border: "028090" },
  { title: "שלב שלישי", body: "תיאור קצר",  bg: "E0F4F6", border: "028090" },
  { title: "שלב רביעי", body: "תיאור קצר",  bg: "E0F4F6", border: "028090" },
], { y: 1.15, h: 1.55, numBg: "028090", arrowColor: "028090" });
```

---

## Title bar helper

Standard full-width title bar across the top of a content slide:

```javascript
function titleBar(s, pres, text, bg = "1E2761", fg = "FFFFFF", h = 1.0) {
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h,
    fill: { color: bg }, line: { color: bg }
  });
  s.addText(text, {
    x: 0.4, y: 0, w: 9.2, h,
    fontFace: "Arial", fontSize: 26, bold: true,
    color: fg, rtlMode: true, align: "right", valign: "middle", margin: 0
  });
}
```

---

## RTL table columns

When building a data table in Hebrew, columns flow right to left.
Define `colX` array from right to left — `colX[0]` is the rightmost (primary) column.

```javascript
// Example: 4-column RTL table
// Columns (RTL): תהליך | לפני | אחרי | חיסכון
const colX = [6.9, 4.5, 2.3, 0.4];  // rightmost first
const colW = [2.8, 2.1, 2.0, 1.7];
const hdrs = ["תהליך", "לפני", "אחרי", "חיסכון"];

hdrs.forEach((h, i) => {
  s.addShape(pres.shapes.RECTANGLE, {
    x: colX[i], y: 1.1, w: colW[i], h: 0.44,
    fill: { color: "1E2761" }, line: { color: "1E2761" }
  });
  s.addText(h, {
    x: colX[i], y: 1.1, w: colW[i], h: 0.44,
    fontFace: "Arial", fontSize: 13, bold: true, color: "FFFFFF",
    rtlMode: true, align: "center", valign: "middle"
  });
});
```

---

## RTL grid (N×M cards)

For a grid where item 1 should be top-right:

```javascript
items.forEach((item, i) => {
  const col = i % COLS;
  const row = Math.floor(i / COLS);

  // RTL: col 0 = rightmost
  const x = slideW - margin - cardW - col * (cardW + gap);
  const y = startY + row * (cardH + rowGap);

  // draw card at (x, y) ...
});
```

---

## Recommended color palette for Hebrew business presentations

```javascript
const C = {
  navy:    "1E2761",   // headers, primary
  navyD:   "141A45",   // dark backgrounds
  teal:    "028090",   // accents, step numbers
  tealL:   "A8DADC",   // light teal
  iceBlue: "CADCFC",   // subtitle text on dark bg
  offWh:   "F4F7FB",   // slide background
  grayL:   "E2E8F0",   // borders, dividers
  gray:    "64748B",   // body text
  green:   "27AE60",   // positive/success
  red:     "E74C3C",   // negative/warning
  orange:  "E67E22",   // highlight/accent
  purple:  "7030A0",   // advanced/secondary
};
```

---

## Shadow — correct syntax

Always use `opacity` (0.0–1.0), **never** encode opacity in the color hex string.

```javascript
// ✅ Correct
shadow: { type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.15 }

// ❌ Wrong — corrupts the file
shadow: { type: "outer", color: "00000026" }
```

Always create a fresh shadow object per shape (pptxgenjs mutates in-place):
```javascript
const makeShadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.15 });
```

---

## Checklist before rendering

- [ ] Every `addText` call with Hebrew text has `rtlMode: true` and `align: "right"`
- [ ] Step 1 is the **rightmost** box (highest x value)
- [ ] Arrows between steps are `"←"` (not `"→"`)
- [ ] Column headers in tables flow right to left (`colX[0]` = rightmost)
- [ ] Grid items: col 0 = rightmost (`x = slideW - margin - cardW - col * (cardW + gap)`)
- [ ] No `"#"` prefix on hex colors
- [ ] Shadow `opacity` is a number (0.0–1.0), not encoded in the color string
- [ ] Fresh shadow object per shape (`makeShadow()` factory, not a shared const)
- [ ] Font is `"Arial"` (renders Hebrew correctly)

---

## QA — visual verification after rendering

```bash
# Convert to images
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 150 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

Then view each slide and check:
- Step 1 is on the **right**
- Arrows point **left** (←)
- All Hebrew text reads naturally right to left
- No text overflow or clipping
