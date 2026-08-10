#!/usr/bin/env node
/*
 * korean-report-skills 설치기
 *
 *   npx github:JangHyun-bin/korean-report-skills            전부에 설치
 *   npx github:JangHyun-bin/korean-report-skills claude     골라서
 *   npx github:JangHyun-bin/korean-report-skills --project  이 저장소에만
 *   npx github:JangHyun-bin/korean-report-skills --remove   제거
 *
 * Claude Code 는 `/plugin marketplace add` 로 설치하는 편이 낫다 — 갱신이 자동이다.
 * 이 설치기는 Codex · Cursor 처럼 플러그인 체계가 없는 도구와,
 * 플러그인을 쓰지 않고 파일로 두고 싶을 때를 위한 것이다.
 */
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const SRC = path.join(ROOT, 'plugins', 'korean-report', 'skills');
const SKILLS = ['korean-report-doc', 'korean-report-style'];
const KNOWN = ['claude', 'codex', 'cursor'];

const argv = process.argv.slice(2);
if (argv.includes('-h') || argv.includes('--help')) {
  console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0].split('/*')[1].trim());
  process.exit(0);
}

const project = argv.includes('--project');
const remove = argv.includes('--remove');
const picked = argv.filter((a) => KNOWN.includes(a));
const agents = picked.length ? picked : KNOWN;

const unknown = argv.filter((a) => !KNOWN.includes(a) && !a.startsWith('--'));
if (unknown.length) {
  console.error(`알 수 없는 인자: ${unknown.join(', ')}`);
  console.error(`쓸 수 있는 값 — ${KNOWN.join(' · ')} · --project · --remove`);
  process.exit(1);
}

if (!fs.existsSync(SRC)) {
  console.error(`스킬 폴더를 찾지 못하였다: ${SRC}`);
  process.exit(1);
}

let done = 0;
for (const agent of agents) {
  const base = project
    ? path.join(process.cwd(), `.${agent}`, 'skills')
    : path.join(os.homedir(), `.${agent}`, 'skills');

  for (const skill of SKILLS) {
    const dest = path.join(base, skill);
    if (remove) {
      if (fs.existsSync(dest)) {
        fs.rmSync(dest, { recursive: true, force: true });
        console.log(`  제거됨  ${dest}`);
        done++;
      }
      continue;
    }
    fs.mkdirSync(base, { recursive: true });
    fs.rmSync(dest, { recursive: true, force: true });
    fs.cpSync(path.join(SRC, skill), dest, { recursive: true });
    if (!fs.existsSync(path.join(dest, 'SKILL.md'))) {
      console.error(`  실패  ${dest} — SKILL.md 가 없다`);
      process.exit(1);
    }
    console.log(`  설치됨  ${dest}`);
    done++;
  }
}

if (!done) {
  console.log(remove ? '제거할 것이 없다.' : '설치된 것이 없다.');
} else if (!remove) {
  console.log('\n완료. 세션을 새로 시작하면 적용된다.');
  console.log('확인 — /skills 를 입력해 목록에 보이는지 본다.');
}
