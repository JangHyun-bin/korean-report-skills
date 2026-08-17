# 디자인 시스템

자립형 HTML 문서(덱·논문)의 시각 규약. `SKILL.md` 가 제작 절차를 다루고,
이 문서가 색·타이포·컴포넌트·인쇄를 정의한다.

Derived from Apple's editorial design language, adapted for Korean typography and for
documents that must survive being exported to PDF, opened offline, and read on paper.

---

## 0. Principles

1. **One accent, everything else monochrome.** Color is a pointer, not decoration. A
   reader should be able to name what the blue means after ten seconds.
2. **The document is the artifact.** No external runtime dependency may change how it
   renders. Math, fonts, and diagrams ship inside the file — including the body face.
   Templates carry no `<link>` to any host; `mathbuild.js` inlines every asset at build
   time (§9). A stylesheet fetched at runtime is a document that renders differently on
   a plane, behind a firewall, and in five years.
3. **Structure is carried by space and weight, not by boxes.** Borders and shadows are
   the last resort, not the first.
4. **Print is a first-class target.** Every rule has a `@media print` counterpart. A
   document that breaks when exported is not finished.
5. **Never imply precision you do not have.** Status must be visible at the point of the
   claim, not buried in a footnote.

---

## 1. Foundations

### 1.1 Color

Monochrome scale plus exactly one accent. Do not introduce a second hue.

```css
:root{
  /* accent — the only chromatic value */
  --primary:      #0066cc;   /* on light surfaces */
  --primary-dark: #2997ff;   /* on dark surfaces  */

  /* ink */
  --ink:    #1d1d1f;         /* body text, strongest rules      */
  --ink80:  #333333;         /* secondary prose                 */
  --ink48:  #7a7a7a;         /* captions, labels, muted numbers */

  /* surfaces */
  --canvas:    #ffffff;
  --parchment: #f5f5f7;      /* alternating tile, code chips    */
  --pearl:     #fafafc;      /* callout fill, blank table cells */
  --tile1:     #272729;      /* dark tile                       */
  --black:     #000000;      /* cover / closing only            */

  /* lines */
  --hairline: #e0e0e0;       /* table rules, card borders       */
  --divider:  #f0f0f0;       /* internal separators             */

  /* highlight — a reading layer, not a second accent (§4.7) */
  --mark:     #fbeaa0;
  --mark-ink: #1d1d1f;       /* fixed; dark tiles must not invert it */
}
```

**Rules**

- `--primary` marks one of: a section number, an eyebrow, a live link, a highlighted
  row, or a single emphasized figure. Not all of them on the same screen.
- On dark tiles the accent switches to `--primary-dark`. The light-surface blue fails
  contrast on `#272729`.
- Red, amber, and green are **not** severity signals here. Severity is expressed by
  border weight and position (§4.3), not by hue.
- **The highlight yellow is not a second accent and may not be used as one.** The accent
  answers *this is the point*; the highlight answers *read this part*. One is the
  author's pointer, the other is a reading layer laid over finished prose. The moment a
  highlight lands on a section number, an eyebrow, or a link, that distinction has
  collapsed and the document has two accents — which is the thing this section forbids.

### 1.2 Typography

Pretendard, globally. It carries Latin and Hangul in one family with consistent metrics,
which SF Pro cannot do.

```css
--font: 'Pretendard','Pretendard Variable',
        -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
--mono: 'SF Mono', ui-monospace, Menlo, Consolas, monospace;
```

Pretendard is **embedded as base64 `@font-face` at build time**, not linked:

```bash
node mathbuild.js raw.html out.html --font Pretendard-Regular.woff2                                     --font Pretendard-SemiBold.woff2
```

The stack above is the fallback chain for the case where a build omits `--font`. That
build still succeeds but emits a warning — the document then renders with whatever the
reader's machine has, and the metrics that make Hangul and Latin align are gone.

| Role | Size | Weight | Line height | Tracking |
|---|---|---|---|---|
| Hero (cover) | `clamp(34px,4.6vw,50px)` | 600 | 1.08 | `-0.028em` |
| Section h2 | 25–34px | 600 | 1.14–1.25 | `-0.012em` |
| Sub-head h3 | 18.5px | 600 | 1.24 | `-0.008em` |
| Lead | `clamp(19px,1.8vw,24px)` | 400 | 1.40 | `+0.196px` |
| Body | 16.5px | 400 | 1.72 | `-0.32px` |
| Table | 14–15px | 400 | 1.55 | `-0.18px` |
| Caption | 13px | 400 | 1.5 | `-0.2px` |
| Eyebrow | 13–14px | 600 | — | `0` |

**Tracking is negative for display sizes and near-zero for small text.** This is the
single most recognizable trait of the system; omitting it makes headlines look loose and
generic.

**Line length.** Paper mode caps the measure at `720px`. Deck mode caps at `1120px`
because deck text is short and scanned, not read.

### 1.3 Spacing & radius

```css
--s-xs:8px; --s-sm:12px; --s-md:17px; --s-lg:24px;
--s-xl:32px; --s-xxl:48px; --s-sec:80px;

--r-sm:8px;    /* chips, small fills   */
--r-md:12px;   /* callouts, cards      */
--r-lg:18px;   /* tiles, large panels  */
--r-pill:9999px;
```

Section padding is `--s-sec` in deck mode, `64px` top-only in paper mode.

### 1.4 Elevation

**There are no shadows.** Separation comes from surface color and hairlines. If an
element needs to float, it is probably the wrong element.

---

## 2. Two modes

The same tokens produce two layouts. Choose before writing, not after.

| | **Deck** | **Paper** |
|---|---|---|
| Use for | meetings, agendas, decisions | analysis, benchmarks, specifications |
| Orientation | landscape | portrait |
| Page mapping | 1 section = 1 page | continuous flow |
| Section chrome | full-bleed tiles, alternating | hairline-ruled headings |
| Text density | one idea per page | full prose |
| Measure | 1120px | 720px |
| Vertical alignment | centered in page | top-aligned, flows |

**Never mix.** A deck with paragraph-length prose reads as a badly formatted report; a
paper with tile backgrounds reads as slides someone printed by mistake.

### 2.1 Deck: tile alternation

Sections are full-bleed bands. The background sequence carries the rhythm:

```
black (cover) → light → parchment → dark → light → parchment → … → black (EOD)
```

- **Dark tiles are reserved for the two or three most consequential sections** — the
  central claim, the gap analysis, the roadmap. Using dark for a routine table wastes it.
- Two adjacent tiles never share a background.
- Cover and closing are `--black`, distinct from the `--tile1` used mid-document.

### 2.2 Paper: continuous flow

No tiles. Hierarchy comes from rules and numbering:

```css
h2{ border-bottom:1px solid var(--ink); padding-bottom:12px;
    display:flex; align-items:baseline; gap:14px }
.sn{ color:var(--primary); font-size:14px; font-weight:600; flex:none }
```

The section number sits in the accent color, outside the heading text, at small size —
it labels without competing.

---

## 3. Document opening

### 3.1 Deck cover

```html
<section class="tile black cover">
  <div class="wrap">
    <h1 class="hero">Document title</h1>
    <div class="rule"></div>
    <div class="meta">Date<br>Organization</div>
  </div>
</section>
```

`.rule` is a 64×1px `#5a5a60` line with `32px` vertical margin. It separates title from
metadata without a heading.

### 3.2 Paper masthead + abstract

```html
<header class="paper-head">
  <p class="eyebrow">Technical Report · YYYY-MM-DD</p>
  <h1>Title</h1>
  <p class="subtitle">Subtitle</p>
  <div class="byline"><span>Team</span><span>Date</span></div>
</header>
<section class="abstract">
  <h2>ABSTRACT</h2>   <!-- 13px, uppercase, tracked +0.06em, no rule -->
  …
</section>
```

The abstract states the finding, the one novel contribution, and **what is missing**, in
that order. The masthead is closed by a `1px solid var(--ink)` rule; the abstract by a
hairline.

---

## 4. Components

### 4.1 Status badges

For documents that report measurement, implementation, or completeness state. Status
appears **inline, at the claim**, never only in a legend.

```css
.bdg{ display:inline-block; font-size:11px; font-weight:600; letter-spacing:0;
      padding:1px 7px; border-radius:var(--r-pill); vertical-align:1.5px;
      white-space:nowrap }
.bdg.meas{ background:var(--primary); color:#fff }              /* measured  */
.bdg.impl{ color:var(--primary); border:1px solid rgba(0,102,204,.5) } /* exists, unused */
.bdg.none{ color:var(--ink48); border:1px dashed var(--ink48) } /* not measured */
.bdg.no  { color:var(--ink48); border:1px solid var(--ink48) }  /* impossible */
```

The encoding is **fill → outline → dashed**, matching confidence. It survives grayscale
printing, which color coding does not.

Define the badges once, near the top, in a `.legend` row. Never use emoji for status:
they render inconsistently across platforms and carry no weight in print.

### 4.2 Tables

```css
th{ text-align:left; font-size:12.5px; font-weight:600; color:var(--ink48);
    border-bottom:1px solid var(--ink); white-space:nowrap }
td{ border-bottom:1px solid var(--hairline); vertical-align:top }
td:first-child, th:first-child{ padding-left:0 }
td:last-child,  th:last-child { padding-right:0 }
tr.hl td{ background:rgba(0,102,204,.045) }
table.num td:not(:first-child){ text-align:right; white-space:nowrap }
```

- **No vertical rules, no zebra striping.** One heavy rule under the header, hairlines
  between rows.
- First and last columns are flush to the measure. Tables are not boxes.
- `table.num` right-aligns every column but the label. Digits must align to compare.
- `tr.hl` marks at most **one** row per table — the reference case or the correction.
- Header labels use `--ink48`, not full ink. The data is the content; the header is
  navigation.

**Wide tables** (7+ columns) get a scroll wrapper that bleeds to the margin on screen and
compresses in print:

```css
.scroll.wide{ margin:24px -24px 8px; padding:0 24px; overflow-x:auto }
@media print{
  .scroll.wide{ overflow:visible; margin:14px 0 6px; padding:0 }
  .scroll.wide table{ font-size:7.4pt }
}
```

### 4.3 Callouts

Four variants, distinguished by **border position and weight** — never by color.

| Variant | Border | Fill | Use |
|---|---|---|---|
| `.note` | 1px all round | `--pearl` | scope limits, methodology caveats |
| `.warn` | 3px left, `--ink` | `#fff` | corrections, things that will mislead |
| `.finding` | 3px left, `--primary` | `#fff` | the document's own conclusions |
| `.claim` | none | `--parchment` | the single defensible statement |

```css
.note,.warn,.finding,.claim{ border-radius:var(--r-md); padding:18px 22px; margin:24px 0 }
.warn   { background:#fff; border:1px solid var(--hairline); border-left:3px solid var(--ink) }
.finding{ background:#fff; border:1px solid rgba(0,102,204,.3); border-left:3px solid var(--primary) }
```

A `.finding` may carry a `.cav` trailer — a hairline-separated line in `--ink48` stating
the limits of the finding. Conclusions and their caveats stay in the same box.

**Heading form.** Callout titles and sub-headings are **noun phrases, not sentences**.
Write `일정 시사점`, not `일정이 말하는 것`; `가드의 정상 동작`, not `가드는 제 역할을 했다`.
Sentence headings read as commentary and age badly when the document is revised; noun
phrases name the topic and let the body carry the claim. Use an em dash to qualify —
`K — 핵심이자 약점`, `상한 2.5 와 공개셋 요구치의 여유`.

Figure titles inside SVG are the exception: they are statements, not headings, and may
be full sentences.

**Prose register.** Body text is expository, not conversational. Two patterns to avoid:

- **Colloquial paraphrase of a technical fact.** Write `검사 장비의 검출 범위`, not
  `검사 장비가 보는 전부`; `모델의 출력`, not `모델이 내는 것`; `절반 수준으로 낮아진다`,
  not `반토막이 된다`; `크기를 재는 편이 비용이 낮다`, not `크기를 재는 것이 싸다`.
- **Anthropomorphism, including domain metaphors.** Semiconductor practice says a die
  *dies* and a defect *kills*, but a delivered document should say
  `다이가 불량으로 판정된다` / `양품이 잔존한다`, not `다이가 죽는다` / `살아남는다`.
  The metaphor is not wrong; it simply breaks register against the surrounding prose.

Terms of art keep their standard form — `킬러 디펙트`, `뉴슨스`, `드리프트` are names, not
metaphors, and translating them costs precision. So `킬러 디펙트가 다이를 죽인다` becomes
`킬러 디펙트가 다이 불량을 유발한다` — **the name stays; only the verb is rewritten.**

**Verb endings.** Use the unclipped literary form throughout: `되었다` not `됐다`,
`하였고` not `했고`, `하였다` not `했다`. The clipped forms read as speech and clash with
the expository register of the surrounding prose. This applies to figure labels and table
cells as well as body text.

### 4.4 Metric cards

For headline numbers. Two per row, never three.

```css
.metric{ border:1px solid var(--hairline); border-radius:var(--r-lg); padding:var(--s-xl) }
.metric .mlabel{ font-size:14px; color:var(--ink48) }
.metric .mval  { font-size:clamp(30px,3.6vw,42px); font-weight:600;
                 letter-spacing:-.02em; line-height:1.05 }
.metric .mnote { font-size:14px; color:var(--ink48) }
.metric.gap    { background:var(--pearl); border-style:dashed }
.metric.gap .mval{ color:var(--ink48) }
```

`.metric.gap` — dashed border, muted value — states an **absent** measurement with the
same visual weight as a present one. Missing data is data.

Place any caveat that qualifies the numbers **immediately below the cards**, not in a
later section. A reader who screenshots the cards must capture the caveat too.

### 4.5 Lists

```css
ul.plain li, ol.concl li{ padding:11px 0 11px 30px; position:relative;
                          border-top:1px solid var(--hairline) }
ul.plain li::before{ content:""; position:absolute; left:8px; top:21px;
                     width:5px; height:5px; border-radius:50%; background:var(--primary) }
ol.concl li::before{ content:counter(c); position:absolute; left:0; top:11px;
                     font-size:12.5px; font-weight:600; color:var(--primary) }
```

Rule-separated rows, accent markers, no native list glyphs. Numbered lists are for
conclusions and priorities — things a reader may cite by index.

### 4.6 Code

```css
pre{ background:var(--tile1); color:#e6e6e8; border-radius:var(--r-md);
     padding:20px 24px; font-family:var(--mono); font-size:12.5px; line-height:1.75 }
pre .c{ color:#8b8b90 }                     /* comments */
code{ background:var(--parchment); padding:1px 5px; border-radius:5px;
      font-size:.86em; letter-spacing:0 }
```

Inline `code` uses parchment on light surfaces, `rgba(255,255,255,.10)` on dark. Reset
`letter-spacing` to `0` — monospace does not want the negative tracking.

In print, `pre` inverts to `--parchment` on `--ink`. Do not print large black fills.

### 4.7 Emphasis

Body emphasis has two instruments and they are not interchangeable.

| | Carries | Rule |
|---|---|---|
| `<b>` | the author's emphasis | weight 600; anywhere the sentence needs it |
| `<mark>` | a reading layer — *read this part* | **at most one per section** |

```css
mark{ background:var(--mark); color:var(--mark-ink);
      padding:1px .16em; border-radius:3px }
```

**The text colour is pinned, not inherited.** Dark tiles flip `--ink` to white; a
`<mark>` that inherits it becomes white type on yellow and stops being readable. This
was confirmed by typesetting both faces — the variant that let the colour inherit failed
on the dark tile while the pinned one survived. Horizontal padding is set in `em` so the
punctuation after a highlight does not drift.

A second highlight in the same section destroys the first, exactly as a second accent
would. If several spans in one section all deserve marking, none of them do — the
section is making more than one point and should be split.

In grayscale print the yellow flattens to the same value as `--parchment`, so a highlight
and a code chip become indistinguishable. That is acceptable: the highlight guides a
reader through the screen copy and never carries a claim on its own. Anything the printed
document must not lose belongs in a badge (§4.1) or a callout (§4.3).

**Italic.** Pretendard ships no italic face. Applied to Hangul, the browser synthesises an
oblique and the strokes break. Italic is therefore restricted to spans declared as Latin:

```css
i,em{ font-style:normal }
i[lang="en"],em[lang="en"]{ font-style:italic }
```

Write `<i lang="en">alpha</i>` for a variable or a scientific name. An undeclared `<i>`
renders upright and nothing happens — a silent no-op is better than slanted Hangul, and
it teaches the rule the first time someone reaches for it. Italic names a *variable*;
`code` names a *literal string*. Both have a place and they are not substitutes.

---

## 5. Figures & diagrams

### 5.1 Native only

**All figures are inline SVG or HTML/CSS.** No raster images, no chart libraries, no
generated PNGs.

Reasons: they stay sharp at any zoom and in print; they inherit the type and color
tokens; they are diffable; and they add no bytes beyond markup.

**Inheritance is not automatic — it is built.** SVG presentation attributes do not read
CSS variables, so `figures.py` emits *classes* (`fi-*` for fill, `st-*` for stroke) and
`base.css` binds those to the tokens:

```css
svg.fig .fi-ink{ fill:var(--ink) }   svg.fig .st-line{ stroke:var(--fig-line) }
```

Hard-coding `fill="#1d1d1f"` costs nothing on white and makes the label invisible on a
`#272729` tile. Set the class; let the tile redefine the token.

**One exception: measured data plotted over real-world imagery.** A floorplan with
hundreds of surveyed camera positions, or a point cloud, cannot be hand-authored as SVG
without fabricating the data. Such a figure may ship as a raster, subject to three rules:

1. **Embed it as a base64 data URI.** The document stays self-contained (§0.2).
2. **Frame it** — `1px var(--hairline)`, `10px` radius, centred, max 820px wide — so it
   reads as an inset plate rather than a native diagram.
3. **Quantify it natively alongside.** The raster shows the shape; a companion SVG or
   table carries the numbers the reader is meant to act on. Never let a raster be the
   only carrier of a decision-relevant figure.

Regenerate such plots with the document's own font where the source pipeline allows it;
a matplotlib default face next to Pretendard is a visible seam.

### 5.2 Discipline

- **Monochrome plus the accent.** A diagram may use `--ink`, `--ink48`, `--fig-line`
  (`#c7ccd2`), `--fig-mid` (`#8695a6`), `--fig-soft` (`#dfe4e9`), `--fig-pale`
  (`#eef3f8`), and `--primary`. That is the whole palette. Every one of them is
  redefined on dark tiles, so the figure follows the surface.
- **Distinguish by form, not hue** — fill vs. outline, solid vs. dashed, weight, size.
  A category legend that relies on color fails in grayscale.
- **The accent marks the one thing the figure exists to show.** If everything is blue,
  nothing is.
- Set `font-family="Pretendard"` explicitly inside `<svg>`; SVG does not inherit it.
- Label sizes: 11px minimum for annotations, 12–13px for axis and node text.
- Never repeat the section heading inside the figure. The caption and heading already
  say it.

### 5.3 Chart conventions

| Type | Convention |
|---|---|
| **Gantt / timeline** | Bars as percentage-positioned absolute divs over a shared track. Confirmed = solid `#c7ccd2`; proposed = `1.5px dashed var(--primary)`; the critical bar = solid `--ink`. Vertical markers: solid for the present, dashed for deadlines, dotted for targets. |
| **Sawtooth / accumulation** | Two panels side by side, same axis scale, differing only in the parameter under discussion. |
| **Scatter with a model** | Plot the identity line `y = x` as `--ink48` dashed; annotate each point with its ratio to the prediction. Two points are enough if the ratio is the finding. |
| **Number line** | Dots on a single rule, labels alternating above and below to avoid collision; a dashed vertical marks the value under scrutiny. |
| **Flow / pipeline** | Rounded rects, `1px #c7ccd2` stroke. One node filled `--tile1` marks the subject. Arrows `#8695a6`, `1.4px`, triangular marker. |
| **Distribution curve** | Single `2.5px --ink` stroke over a `#dfe4e9` fill; shaded bands for regions of interest. Never a gradient. |

### 5.4 Captions

```html
<svg class="fig">…</svg>
<p class="figcap">그림 3 · 절대보정 간격이 꼬리 오차에 미치는 영향 (개념도)</p>
```

```css
.figcap{ font-size:13px; color:var(--ink48); text-align:center;
         margin:6px 0 26px; letter-spacing:-.2px }
```

Numbered, centered, muted. Use a middot to separate the number from the description.
Tables take `표 n ·` captions **below** the table, matching figures.

Mark schematic figures explicitly — `(개념도)` / `(conceptual)`. A reader must never
mistake an illustration for measured data.

---

## 6. Mathematics

### 6.1 Render at build time

Do **not** ship a runtime math renderer. Render with KaTeX during the build and embed
the resulting markup.

```js
const katex = require('katex');
html = html.replace(/⟦D⟧([\s\S]*?)⟦\/D⟧/g,
        (_, tex) => katex.renderToString(tex, {displayMode:true,  throwOnError:true}));
html = html.replace(/⟦I⟧([\s\S]*?)⟦\/I⟧/g,
        (_, tex) => katex.renderToString(tex, {displayMode:false, throwOnError:true}));
```

**The delimiters are `⟦I⟧` and `⟦D⟧`, not ASCII.** A `%%`-style delimiter collides with
the generator's own `%s`/`%%` substitution: a one-character formula `I("D")` produces the
literal `%%D%%`, which the parser then reads as a display marker. `mathbuild.js` fails the
build if it finds legacy markers.

Use `throwOnError:true` and fail the build loudly — `mathbuild.js` exits non-zero on any
render failure. A silently mis-rendered formula is worse than no formula.

### 6.2 Embed the fonts

Inline only the `woff2` faces the rendered output actually references, as data URIs.
The full KaTeX font set is ~1.2 MB; a typical document needs ~160 KB. Families reached
only through a CSS class (`Size1`–`Size4`, `AMS`) cannot be detected by scanning the
HTML for family names — keep those unconditionally and detect the rest by the classes
that call them (`mathcal`, `mathfrak`, `mathsf`, `mathscr`, `mathtt`).

```js
const used = new Set();
let m, re = /KaTeX_([A-Za-z0-9]+)/g;
while ((m = re.exec(html))) used.add('KaTeX_' + m[1]);
// drop unused faces; base64 the rest into katex.min.css
```

Result: a single HTML file whose math is identical offline, on any machine, in print.

### 6.3 Usage

- **Inline** for symbols referenced in prose — `\varepsilon`, `\rho_0`, `K`.
  Introduce every symbol in prose before it appears in a display equation.
- **Display** for relations the reader must hold in mind. Aim for under one display
  equation per screen of prose.
- **Never place a display equation inside a table cell.** It forces a line break and
  destroys row rhythm. Use inline form.
- Use `\texttt{}` for parameter and file names inside math so they match `code`.
- `\underbrace{…}_{\text{label}}` is the preferred way to contrast two models in one line.

```css
.katex-display{ margin:22px 0; overflow-x:auto; overflow-y:hidden }
.katex{ font-size:1.02em }
table.num td .katex{ font-size:.94em }
```

A notation table at the end, listing every symbol once, is mandatory for any document
with more than five equations.

---

## 7. Print

Both modes must export cleanly with browser print-to-PDF at zero margins.

**Each mode owns exactly one `@media print` block**, in `css/paper.css` or `css/deck.css`.
Never copy print rules between them. When both templates carried their own copy, the deck
picked up the paper block last and printed a 34pt hero next to a 14pt heading.

### 7.1 Deck

One section, one page, contents vertically centered so leftover space splits evenly.

```css
@media print{
  @page{ size:A4 landscape; margin:0 }
  .nav{ display:none }
  .tile{ height:210mm; padding:14mm 16mm;
         display:flex; align-items:center;
         page-break-after:always; break-inside:avoid; overflow:hidden }
  .tile:last-child{ break-after:auto }
  .wrap{ width:100%; max-width:none }
}
```

If a section overflows one page, **split the section** — do not shrink type below the
scale. Two clean pages beat one crowded one.

`overflow:hidden` means an overflowing tile is **silently truncated**, not visibly broken —
which is why `assets/qa.py` measures every tile against the page height under
`print` media and fails the build. This is the single most common deck defect.

### 7.2 Paper

Continuous flow with break control.

```css
@media print{
  @page{ size:A4; margin:18mm 16mm }
  body{ font-size:9.8pt; line-height:1.6 }
  h2,h3,h4{ break-after:avoid }
  p,li{ orphans:3; widows:3 }
  table,pre,.note,.warn,.finding,.claim,.quote-box,
  .katex-display,svg,.figcap{ break-inside:avoid }
  svg{ break-after:avoid }          /* keep figure with its caption */
}
```

### 7.3 Dark tiles in print

Invert them. Never print large dark fills.

```css
@media print{
  .tile.dark,.tile.black{ background:#fff!important; color:#000!important }
  .dark .eyebrow{ color:var(--primary)!important }
  .dark table th{ color:var(--ink48)!important; border-bottom-color:var(--ink)!important }
  .dark .bdg.meas{ background:var(--primary)!important; color:#fff!important }
}
```

### 7.4 Always

```css
*{ -webkit-print-color-adjust:exact; print-color-adjust:exact }
```

Without it, browsers strip the backgrounds that carry the accent and the highlighted rows.

---

## 8. Closing — EOD

Every document ends with a terminal marker and nothing else.

**Deck**

```html
<section class="tile black">
  <div class="wrap">
    <p style="font-size:14px;font-weight:600;letter-spacing:.08em;color:#8b8b90">EOD</p>
  </div>
</section>
```

**Paper**

```html
<footer style="max-width:720px;margin:80px auto 0;padding-top:20px;
               border-top:1px solid var(--hairline);
               font-size:12px;letter-spacing:.08em;color:#7a7a7a">EOD</footer>
```

**Rules**

- The mark is `EOD`, uppercase, positively tracked at `0.08em`, in `--ink48` or
  `#8b8b90`. It is a marker, not a heading.
- **No valediction, no organization name, no logo, no thanks.** The document ends where
  the content ends; the mark only confirms nothing was truncated.
- Deck: a full black page, left-aligned, matching the cover. Paper: a hairline-ruled
  footer.
- The mark is never preceded by a summary. If a summary is needed, it is a section.

---

## 9. Build pipeline

```
data ──▶ generator (Python) ──▶ raw HTML with math markers
                                      │
                                      ▼
                          post-processor (Node + KaTeX)
                          · render ⟦I⟧ / ⟦D⟧
                          · inject base.css + mode css
                          · inline Pretendard + used KaTeX woff2 as data URI
                                      │
                                      ▼
                              single .html  ──▶ headless print ──▶ .pdf
```

Compute figure geometry — bar offsets, curve paths, axis ticks — in the generator and
emit literal SVG coordinates. Do not compute layout in browser JavaScript: it will not
run identically during PDF export.

---

## 10. QA checklist

Run before delivering. Screenshot the rendered output; do not trust the source.
`assets/qa.py` performs the structural block automatically and exits non-zero on failure.

**Structural**
- [ ] No unrendered template or math markers survive in the DOM
- [ ] `document.documentElement.scrollWidth <= window.innerWidth` — no horizontal overflow
- [ ] Every table fits its container: `table.scrollWidth <= parent.clientWidth`
- [ ] KaTeX node count equals the number of formulas authored

**Print**
- [ ] Page count matches intent (deck: sections = pages)
- [ ] No page is cut mid-table, mid-equation, or mid-callout
- [ ] No page is more than half empty
- [ ] No heading is orphaned at the foot of a page
- [ ] Dark tiles inverted; highlighted rows still visible

**Editorial**
- [ ] Exactly one accent hue present
- [ ] Every figure caption numbered; schematics marked as such
- [ ] Any raster figure is base64-embedded, framed, and paired with native quantification
- [ ] Every status claim carries a badge at the claim, not only in the legend
- [ ] At most one `<mark>` per section, and none on a heading, number, or link
- [ ] Italic appears only inside a span declared `lang="en"`
- [ ] Callout and sub-heading titles are noun phrases, not sentences
- [ ] No colloquial paraphrase or anthropomorphism in body prose
- [ ] Verb endings use the unclipped literary form (`되었다`, `하였고`)
- [ ] Notation table present if equations > 5
- [ ] Document ends with `EOD` and nothing after it

---

## 11. Anti-patterns

| Do not | Because |
|---|---|
| Add a second accent color | Destroys the pointer function of the first |
| Highlight several spans in one section | The marker stops marking; same failure as a second accent |
| Let `<mark>` inherit its text color | Dark tiles flip `--ink` to white, leaving white type on yellow |
| Italicise Hangul | No italic face exists; the synthesised oblique breaks the strokes |
| Use red/amber/green for severity | Fails grayscale print; the border system already encodes it |
| Use emoji as status markers | Platform-inconsistent, weightless in print |
| Put a display equation in a table cell | Breaks row rhythm and column alignment |
| Load fonts or math from a CDN at runtime | The document stops being self-contained |
| Reference a raster figure by relative path | Same — the file breaks when moved |
| Repeat the section title inside a figure | Duplicates the caption; wastes the figure's top |
| Add shadows to lift a card | Nothing in this system floats |
| Write callout titles as sentences | Headings name the topic; the body makes the claim |
| Paraphrase a technical fact colloquially | Register break; the fact reads as an aside |
| Anthropomorphise components | Metaphor clashes with the surrounding expository prose |
| Shrink type to fit one more page | Split the section instead |
| Close with "Thank you" or a logo | The document ends at `EOD` |
| Zebra-stripe or vertically rule a table | Hairlines and alignment are sufficient |
| Fill a deck page with paragraphs | That is paper mode; choose the right mode |

---

*EOD*
