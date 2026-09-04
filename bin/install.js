#!/usr/bin/env node
/* korean-report-skills의 Claude Code·Codex·Cursor 파일 복사 설치기. */
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HELP = `korean-report-skills 파일 복사 설치기

사용법:
  npx korean-report-skills [claude|codex|cursor]... [--project] [--remove]

예:
  npx korean-report-skills            Claude Code·Codex·Cursor에 설치
  npx korean-report-skills cursor     Cursor에만 설치
  npx korean-report-skills --project  현재 프로젝트에 설치
  npx korean-report-skills --remove   복사한 스킬 제거

Claude Code와 Codex는 plugin marketplace 설치도 지원합니다.
특정 GitHub revision: npx github:JangHyun-bin/korean-report-skills cursor`;

const ROOT = path.join(__dirname, '..');
const SRC = path.join(ROOT, 'plugins', 'korean-report', 'skills');
const SKILLS = ['korean-report-doc', 'korean-report-style'];
const KNOWN = ['claude', 'codex', 'cursor'];

const argv = process.argv.slice(2);
if (argv.includes('-h') || argv.includes('--help')) {
  console.log(HELP);
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
  console.error(`스킬 폴더를 찾지 못하였습니다: ${SRC}`);
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
      console.error(`  실패  ${dest} — SKILL.md 가 없습니다`);
      process.exit(1);
    }
    console.log(`  설치됨  ${dest}`);
    done++;
  }
}

if (!done) {
  console.log(remove ? '제거할 것이 없습니다.' : '설치된 것이 없습니다.');
} else if (!remove) {
  console.log('\n완료하였습니다. 세션을 새로 시작하면 적용됩니다.');
  console.log('/skills 를 입력해 목록에 보이는지 확인해 주세요.');
}
