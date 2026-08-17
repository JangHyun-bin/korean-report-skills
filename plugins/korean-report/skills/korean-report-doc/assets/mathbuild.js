#!/usr/bin/env node
/*
 * mathbuild.js — raw HTML 을 자립형 단일 HTML 로 만든다.
 *
 *   node mathbuild.js raw.html out.html [--font <woff2>[:weight]]... [--assets <dir>]
 *
 * 하는 일
 *   1. ⟦I⟧ / ⟦D⟧ 마커를 KaTeX 로 렌더한다 (빌드 시점)
 *   2. 렌더 결과가 실제로 참조하는 woff2 만 골라 base64 로 내장한다
 *   3. base.css 와 모드 CSS(paper/deck)를 <html data-mode> 를 보고 삽입한다
 *   4. --font 로 준 Pretendard woff2 를 @font-face 로 내장한다
 *
 * 실패하면 exit 1 이다. 조용히 잘못 렌더된 수식이 수식 없는 것보다 나쁘다.
 */
'use strict';
const fs = require('fs');
const path = require('path');

// 스킬은 ~/.claude/skills 같은 곳에 복사되므로, 이 파일의 위치를 기준으로만
// require('katex') 하면 사용자의 작업 프로젝트에 설치한 KaTeX 를 찾지 못한다.
// 작업 디렉터리를 먼저 보고, npm plugin처럼 스킬 쪽에 의존성이 딸려 온 경우를
// 위해 스크립트 위치를 다음 후보로 본다.
function loadKatex() {
  const roots = [...new Set([process.cwd(), __dirname].map(p => path.resolve(p)))];
  const errors = [];
  for (const root of roots) {
    try {
      const main = require.resolve('katex', { paths: [root] });
      const manifest = require.resolve('katex/package.json', { paths: [root] });
      const dist = path.join(path.dirname(manifest), 'dist');
      if (!fs.existsSync(path.join(dist, 'katex.min.css'))) {
        errors.push(`${root} (katex.min.css 없음)`);
        continue;
      }
      return { api: require(main), dist };
    } catch (e) {
      errors.push(`${root} (${e.code || e.message})`);
    }
  }
  throw new Error(
    `katex 를 찾을 수 없다 — 작업 디렉터리에서 npm install katex\n  검색: ${errors.join('\n  검색: ')}`,
  );
}

let katexRuntime;
try {
  katexRuntime = loadKatex();
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
const katex = katexRuntime.api;

// ── 인자 ───────────────────────────────────────────────────
const argv = process.argv.slice(2);
const fonts = [];
let assetsDir = __dirname;
const positional = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--font') { fonts.push(argv[++i]); }
  else if (argv[i] === '--assets') { assetsDir = argv[++i]; }
  else if (argv[i] === '-h' || argv[i] === '--help') {
    console.log('사용법: node mathbuild.js <in.html> <out.html> [--font <woff2>[:weight]]... [--assets <dir>]');
    process.exit(0);
  } else { positional.push(argv[i]); }
}
const IN = positional[0] || 'raw.html';
const OUT = positional[1] || 'out.html';

const fail = [];
const warn = [];
let html = fs.readFileSync(IN, 'utf8');

// 문자열 치환에서 $& · $' 같은 패턴이 해석되지 않게 항상 함수 replacer 를 쓴다
const put = (h, marker, value) => h.replace(marker, () => value);

// ── 1. 수식 렌더링 ─────────────────────────────────────────
let nInline = 0, nBlock = 0;
const bad = [];
html = html.replace(/⟦D⟧([\s\S]*?)⟦\/D⟧/g, (_, tex) => {
  nBlock++;
  try { return katex.renderToString(tex, { displayMode: true, throwOnError: true, strict: false }); }
  catch (e) { bad.push(['D', tex, e.message]); return '<code>' + tex + '</code>'; }
});
html = html.replace(/⟦I⟧([\s\S]*?)⟦\/I⟧/g, (_, tex) => {
  nInline++;
  try { return katex.renderToString(tex, { displayMode: false, throwOnError: true, strict: false }); }
  catch (e) { bad.push(['I', tex, e.message]); return '<code>' + tex + '</code>'; }
});
console.log(`수식 — display ${nBlock} · inline ${nInline}`);
if (bad.length) {
  bad.forEach(f => fail.push(`수식 렌더 실패 [${f[0]}] ${f[1]} → ${f[2]}`));
}

// ── 2. 잔존 마커 검사 ──────────────────────────────────────
// design.md 구버전의 %%I%% 계열을 쓰면 여기서 잡힌다. 렌더되지 않고 그대로 출력되기 때문이다.
if (/%%\/?[ID]%%/.test(html)) {
  fail.push('구버전 ASCII 수식 마커(%%I%% · %%D%%)가 남아 있다 — ⟦I⟧ · ⟦D⟧ 를 쓴다');
}
if (/⟦\/?[ID]⟧/.test(html)) {
  fail.push('짝이 맞지 않는 수식 마커(⟦I⟧ · ⟦D⟧)가 남아 있다');
}
for (const ph of ['__BODY__', '__TITLE__']) {
  if (html.includes(ph)) fail.push(`템플릿 플레이스홀더 ${ph} 가 치환되지 않았다`);
}

// ── 3. KaTeX CSS — 실제로 쓰이는 계열만 내장 ───────────────
function katexDist() {
  return katexRuntime.dist;
}
const dist = katexDist();
let css = fs.readFileSync(path.join(dist, 'katex.min.css'), 'utf8');

// 항상 필요한 계열. Size1~4 와 AMS 는 클래스로만 참조되어 HTML 스캔으로 잡히지 않는다.
const used = new Set(['KaTeX_Main', 'KaTeX_Math', 'KaTeX_Size1', 'KaTeX_Size2',
                      'KaTeX_Size3', 'KaTeX_Size4', 'KaTeX_AMS']);
// 선택적 계열은 그 계열을 부르는 클래스가 출력에 있을 때만 넣는다
const optional = {
  KaTeX_Caligraphic: /\bmathcal\b/,
  KaTeX_Fraktur:     /\bmathfrak\b/,
  KaTeX_SansSerif:   /\b(mathsf|textsf)\b/,
  KaTeX_Script:      /\bmathscr\b/,
  KaTeX_Typewriter:  /\b(mathtt|texttt)\b/,
};
for (const [fam, re] of Object.entries(optional)) if (re.test(html)) used.add(fam);

let inlined = 0, dropped = 0, fontBytes = 0;
css = css.replace(/src:([^;]+);/g, (whole, src) => {
  const fileMatch = src.match(/fonts\/(KaTeX_[A-Za-z0-9\-]+)\.woff2/);
  if (!fileMatch) return whole;
  const base = fileMatch[1];
  const fam = 'KaTeX_' + base.split('_')[1].split('-')[0];
  const p = path.join(dist, 'fonts', base + '.woff2');
  if (!used.has(fam) || !fs.existsSync(p)) { dropped++; return 'src:local("' + base + '");'; }
  const buf = fs.readFileSync(p);
  fontBytes += buf.length;
  inlined++;
  return `src:url(data:font/woff2;base64,${buf.toString('base64')}) format("woff2");`;
});
console.log(`KaTeX 폰트 — 내장 ${inlined} · 제외 ${dropped} (${(fontBytes / 1024).toFixed(0)} KB)`);
html = put(html, '__KATEXCSS__', css);

// ── 4. 본문 폰트 (Pretendard) 내장 ─────────────────────────
const WEIGHTS = { thin:100, extralight:200, light:300, regular:400, medium:500,
                  semibold:600, bold:700, extrabold:800, black:900 };
let fontCss = '';
if (fonts.length) {
  let n = 0, bytes = 0;
  for (const spec of fonts) {
    const [fp, wExplicit] = spec.split(/:(?=[^:\\/]*$)/);
    if (!fs.existsSync(fp)) { fail.push(`--font 경로가 없다: ${fp}`); continue; }
    const stem = path.basename(fp, path.extname(fp));
    const isVar = /variable/i.test(stem);
    const suffix = (stem.split('-')[1] || 'Regular').toLowerCase();
    const weight = wExplicit || (isVar ? '45 920' : (WEIGHTS[suffix] || 400));
    const buf = fs.readFileSync(fp);
    bytes += buf.length; n++;
    fontCss += `@font-face{font-family:'Pretendard';font-style:normal;font-weight:${weight};` +
               `font-display:swap;src:url(data:font/woff2;base64,${buf.toString('base64')}) format("woff2")}\n`;
  }
  console.log(`본문 폰트 — 내장 ${n} (${(bytes / 1024).toFixed(0)} KB)`);
} else {
  warn.push('Pretendard 미내장 — 시스템 폰트로 폴백한다. 오프라인·타 기기에서 typesetting 결과가 달라진다. ' +
            '--font 로 woff2 를 지정한다.');
}
html = put(html, '__FONTCSS__', fontCss);

// ── 5. 문서 CSS — data-mode 를 보고 고른다 ─────────────────
const modeMatch = html.match(/<html[^>]*\bdata-mode="(paper|deck)"/);
if (!modeMatch) {
  fail.push('<html data-mode="paper|deck"> 가 없다 — 어떤 모드 CSS 를 넣을지 알 수 없다');
} else {
  const mode = modeMatch[1];
  const read = f => fs.readFileSync(path.join(assetsDir, 'css', f), 'utf8');
  html = put(html, '__BASECSS__', read('base.css'));
  html = put(html, '__MODECSS__', read(`${mode}.css`));
  console.log(`모드 — ${mode}`);
}
for (const ph of ['__BASECSS__', '__MODECSS__', '__FONTCSS__', '__KATEXCSS__']) {
  if (html.includes(ph)) fail.push(`CSS 플레이스홀더 ${ph} 가 치환되지 않았다`);
}

// ── 6. 제3자 자산 고지 ─────────────────────────────────────
// 글꼴을 base64 로 내장하는 것은 그 사본을 문서와 함께 배포하는 것이다.
// OFL·MIT 모두 고지 동반을 요구하므로 산출물 자신이 고지를 싣는다.
{
  const notices = ['  · KaTeX 수식 글꼴 — MIT License — https://github.com/KaTeX/KaTeX'];
  if (fontCss) {
    notices.push('  · Pretendard 본문 글꼴 — SIL Open Font License 1.1 — ' +
                 'https://github.com/orioncactus/pretendard');
  }
  const notice = `<!--\n  이 문서에 내장된 제3자 자산\n${notices.join('\n')}\n-->\n`;
  if (html.includes('</head>')) {
    html = put(html, '</head>', notice + '</head>');
  } else {
    warn.push('</head> 를 찾지 못해 제3자 자산 고지를 넣지 못하였다');
  }
}

// ── 7. 결과 ────────────────────────────────────────────────
warn.forEach(w => console.warn('  WARN  ' + w));
if (fail.length) {
  console.error('\n빌드 실패:');
  fail.forEach(f => console.error('  ERROR ' + f));
  process.exit(1);
}
fs.writeFileSync(OUT, html);
console.log(`${OUT} — ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
