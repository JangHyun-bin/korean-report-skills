/*
 * mathbuild.js 의 계약 — 특히 "실패하면 exit 1" 이다.
 *
 * 원래 이 빌더는 수식 오류를 catch 로 삼키고 exit 0 으로 끝냈다.
 * SKILL.md 는 "빌드가 실패하게 한다"고 적혀 있었으므로 문서와 코드가 어긋나 있었다.
 * 여기서 그 계약을 고정한다.
 */
'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const ASSETS = path.join(ROOT, 'plugins', 'korean-report', 'skills', 'korean-report-doc', 'assets');
const BUILD = path.join(ASSETS, 'mathbuild.js');

let tmpSeq = 0;
function tmpdir() {
  const d = path.join(os.tmpdir(), `mathbuild-test-${process.pid}-${tmpSeq++}`);
  fs.mkdirSync(d, { recursive: true });
  return d;
}

function template(mode = 'paper') {
  return fs.readFileSync(path.join(ASSETS, `${mode}_template.html`), 'utf8');
}

/** 템플릿에 본문을 넣어 raw 를 만들고 빌드한다. */
function build(body, { mode = 'paper', title = 'T', args = [], raw = null } = {}) {
  const d = tmpdir();
  const inFile = path.join(d, 'raw.html');
  const outFile = path.join(d, 'out.html');
  const html = raw !== null
    ? raw
    : template(mode).replace('__BODY__', body).replace('__TITLE__', title);
  fs.writeFileSync(inFile, html, 'utf8');
  const r = spawnSync(process.execPath, [BUILD, inFile, outFile, '--assets', ASSETS, ...args],
                      { encoding: 'utf8' });
  return {
    ...r,
    out: fs.existsSync(outFile) ? fs.readFileSync(outFile, 'utf8') : null,
    outFile,
  };
}

test('정상 입력이면 exit 0 이고 수식이 렌더된다', () => {
  const r = build('<section><p>잔차 ⟦I⟧\\varepsilon⟦/I⟧ 는 ⟦D⟧x^2 + y^2⟦/D⟧ 다.</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /class="katex/);
  assert.ok(!r.out.includes('⟦'), '수식 마커가 남았다');
});

test('CSS 네 자리가 모두 채워진다', () => {
  const r = build('<section><p>본문</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  for (const ph of ['__FONTCSS__', '__KATEXCSS__', '__BASECSS__', '__MODECSS__']) {
    assert.ok(!r.out.includes(ph), `${ph} 가 남았다`);
  }
  assert.match(r.out, /--primary:#0066cc/, 'base.css 가 들어가지 않았다');
});

test('모드에 맞는 CSS 를 고른다', () => {
  const paper = build('<section><p>x</p></section>', { mode: 'paper' });
  const deck = build('<section class="tile light"><div class="wrap"><p>x</p></div></section>',
                     { mode: 'deck' });
  assert.match(paper.out, /--w:720px/);
  assert.ok(!paper.out.includes('height:210mm'), 'paper 에 deck 인쇄 규칙이 섞였다');
  assert.match(deck.out, /--w:1120px/);
  assert.match(deck.out, /height:210mm/, 'deck 에 1섹션=1페이지 규칙이 없다');
});

test('수식 오류는 빌드를 세운다', () => {
  const r = build('<section><p>⟦D⟧\\frac{1}{⟦/D⟧</p></section>');
  assert.strictEqual(r.status, 1, '수식이 깨졌는데 빌드가 통과했다');
  assert.match(r.stderr, /수식 렌더 실패/);
});

test('구버전 ASCII 마커는 빌드를 세운다', () => {
  const r = build('<section><p>%%D%%x^2%%/D%%</p></section>');
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /구버전 ASCII 수식 마커/);
});

test('짝이 맞지 않는 마커는 빌드를 세운다', () => {
  const r = build('<section><p>⟦D⟧x^2</p></section>');
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /짝이 맞지 않는/);
});

test('치환되지 않은 토큰은 빌드를 세운다', () => {
  const r = build(null, { raw: template('paper').replace('__TITLE__', 'T') });
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /__BODY__/);
});

test('data-mode 가 없으면 빌드를 세운다', () => {
  const raw = template('paper')
    .replace('data-mode="paper"', '')
    .replace('__BODY__', '<p>x</p>').replace('__TITLE__', 'T');
  const r = build(null, { raw });
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /data-mode/);
});

test('없는 폰트 경로는 빌드를 세운다', () => {
  const r = build('<section><p>x</p></section>', { args: ['--font', 'no-such-font.woff2'] });
  assert.strictEqual(r.status, 1);
  assert.match(r.stderr, /--font 경로가 없다/);
});

test('폰트를 주지 않으면 경고만 하고 통과한다', () => {
  const r = build('<section><p>x</p></section>');
  assert.strictEqual(r.status, 0);
  assert.match(r.stderr + r.stdout, /Pretendard 미내장/);
});

test('폰트를 주면 @font-face 로 내장된다', () => {
  const d = tmpdir();
  const fake = path.join(d, 'Pretendard-SemiBold.woff2');
  fs.writeFileSync(fake, Buffer.from('wOF2fake-payload'));
  const r = build('<section><p>x</p></section>', { args: ['--font', fake] });
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /@font-face\{font-family:'Pretendard'/);
  assert.match(r.out, /font-weight:600/, '파일명에서 굵기를 읽지 못했다');
  assert.match(r.out, /url\(data:font\/woff2;base64,/);
  assert.ok(!(r.stderr + r.stdout).includes('Pretendard 미내장'));
});

test('KaTeX 폰트는 쓰이는 계열만 내장한다', () => {
  const r = build('<section><p>⟦I⟧x⟦/I⟧</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.stdout, /KaTeX 폰트 — 내장 \d+ · 제외 [1-9]/, '제외된 계열이 없다');
});

test('내장한 글꼴의 라이선스를 문서가 스스로 고지한다', () => {
  const r = build('<section><p>x</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /이 문서에 내장된 제3자 자산/);
  assert.match(r.out, /KaTeX.*MIT License/);
  assert.ok(!r.out.includes('Pretendard 본문 글꼴'),
            '본문 글꼴을 내장하지 않았는데 고지가 들어갔다');
});

test('본문 글꼴을 내장하면 OFL 고지가 함께 들어간다', () => {
  const d = tmpdir();
  const fake = path.join(d, 'Pretendard-Regular.woff2');
  fs.writeFileSync(fake, Buffer.from('wOF2fake-payload'));
  const r = build('<section><p>x</p></section>', { args: ['--font', fake] });
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /Pretendard 본문 글꼴 — SIL Open Font License 1\.1/);
});

test('실패한 빌드는 출력 파일을 쓰지 않는다', () => {
  const r = build('<section><p>⟦D⟧\\frac{1}{⟦/D⟧</p></section>');
  assert.strictEqual(r.status, 1);
  assert.strictEqual(r.out, null, '실패했는데 out.html 이 만들어졌다');
});
