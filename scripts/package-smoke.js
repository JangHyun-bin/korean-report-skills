#!/usr/bin/env node
/* npm tarball의 공개 진입점·스크립트·문서 자산과 OpenCode hook을 검사한다. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { spawnSync } = require('node:child_process');

const ROOT = path.join(__dirname, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';

function fail(message) {
  console.error(`패키지 smoke 실패 — ${message}`);
  process.exit(1);
}

function normalize(rel) {
  return rel.replace(/^\.\//, '').replaceAll('\\', '/').replace(/\/$/, '');
}

function packedHas(files, rel) {
  const wanted = normalize(rel);
  return files.has(wanted) || [...files].some((file) => file.startsWith(`${wanted}/`));
}

const packed = spawnSync(npm, ['pack', '--dry-run', '--json'], {
  cwd: ROOT,
  encoding: 'utf8',
  env: { ...process.env, npm_config_loglevel: 'error' },
});
if (packed.status !== 0) fail(`npm pack 실패\n${packed.stderr || packed.stdout}`);

let manifest;
try {
  manifest = JSON.parse(packed.stdout)[0];
} catch (error) {
  fail(`npm pack JSON을 읽지 못하였다 — ${error.message}`);
}
const files = new Set(manifest.files.map((entry) => normalize(entry.path)));
const generatedPython = [...files].filter((file) =>
  file.includes('/__pycache__/') || /\.py[co]$/.test(file));
if (generatedPython.length) {
  fail(`Python cache가 tarball에 포함됨: ${generatedPython.join(', ')}`);
}

const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8');
const readmeRefs = [
  ...[...readme.matchAll(/\b(?:src|srcset)="([^"]+)"/g)].map((match) => match[1]),
  ...[...readme.matchAll(/\]\(([^)]+)\)/g)].map((match) => match[1]),
]
  .map((ref) => ref.split(/[?#]/, 1)[0])
  .filter((ref) => ref && !/^(?:[a-z]+:|#|\/|\.\.\/)/i.test(ref));

const required = [
  'package.json',
  pkg.main,
  ...Object.values(pkg.exports),
  ...Object.values(pkg.bin),
  '.claude-plugin/marketplace.json',
  'plugins/korean-report/.claude-plugin/plugin.json',
  'plugins/korean-report/skills/korean-report-doc/SKILL.md',
  'plugins/korean-report/skills/korean-report-doc/assets/mathbuild.js',
  'plugins/korean-report/skills/korean-report-doc/assets/qa.py',
  'plugins/korean-report/skills/korean-report-doc/assets/figures.py',
  'plugins/korean-report/skills/korean-report-style/SKILL.md',
  'plugins/korean-report/skills/korean-report-style/assets/lint.py',
  'README.md', 'INSTALL.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
  'docs/assets/logo.svg', 'docs/assets/banner-light.png', 'docs/assets/banner-dark.png',
  'docs/assets/ba_before.png', 'docs/assets/ba_after.png', 'docs/assets/ba_after_body.png',
  'examples/before_after.md', 'examples/build_example.py',
  'tests/mathbuild.test.js', 'tests/test_build_e2e.py', 'pyproject.toml',
  ...readmeRefs,
];

const localScriptRefs = [];
for (const command of Object.values(pkg.scripts)) {
  for (const match of command.matchAll(/(?:^|\s)((?:bin|scripts|examples|tests)\/[^\s;&]+)/g)) {
    localScriptRefs.push(match[1]);
  }
}

const missing = [...new Set([...required, ...localScriptRefs])]
  .filter((rel) => !packedHas(files, rel));
if (missing.length) fail(`tarball 누락: ${missing.join(', ')}`);

const installerHelp = spawnSync(process.execPath, [path.join(ROOT, normalize(pkg.bin['korean-report-skills'])), '--help'], {
  cwd: ROOT,
  encoding: 'utf8',
});
if (installerHelp.status !== 0 || !installerHelp.stdout.includes('npx korean-report-skills')) {
  fail(`설치기 도움말이 npm 실행 경로를 안내하지 않는다\n${installerHelp.stderr || installerHelp.stdout}`);
}

async function checkOpenCode() {
  const entry = path.join(ROOT, normalize(pkg.main));
  const module = await import(pathToFileURL(entry).href);
  if (typeof module.default !== 'function') fail('OpenCode default export가 함수가 아니다');

  const hooks = await module.default({});
  if (!hooks || typeof hooks.config !== 'function') fail('OpenCode config hook이 없다');

  const config = {};
  await hooks.config(config);
  const paths = config.skills && config.skills.paths;
  if (!Array.isArray(paths) || paths.length !== 1) fail('OpenCode hook이 skills.paths를 등록하지 않았다');

  const skillNames = fs.readdirSync(paths[0])
    .filter((name) => fs.existsSync(path.join(paths[0], name, 'SKILL.md')))
    .sort();
  const expected = ['korean-report-doc', 'korean-report-style'];
  if (JSON.stringify(skillNames) !== JSON.stringify(expected)) {
    fail(`OpenCode 배포 스킬이 어긋난다 — ${skillNames.join(', ')}`);
  }

  await hooks.config(config);
  if (config.skills.paths.length !== 1) fail('OpenCode hook이 같은 경로를 중복 등록한다');
}

checkOpenCode()
  .then(() => console.log(`패키지 smoke 통과 — ${manifest.entryCount} files · ${manifest.size} bytes`))
  .catch((error) => fail(error.stack || error.message));
