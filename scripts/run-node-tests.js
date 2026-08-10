#!/usr/bin/env node
/*
 * tests/ 의 *.test.js 를 찾아 node --test 로 돌린다.
 *
 * `node --test "tests/*.test.js"` 를 바로 쓰지 않는 이유 — 글로브 해석 주체가
 * 환경마다 다르다. Node 22 는 스스로 풀지만 Node 20 은 리터럴 경로로 보고,
 * bash 는 풀지만 cmd 는 풀지 않는다. 여기서 직접 찾으면 그 차이가 사라진다.
 */
'use strict';
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const dir = path.join(__dirname, '..', 'tests');
const files = fs.readdirSync(dir)
  .filter((f) => f.endsWith('.test.js'))
  .sort()
  .map((f) => path.join(dir, f));

if (files.length === 0) {
  console.error(`검사 파일이 없다 — ${dir}/*.test.js`);
  process.exit(1);
}

const r = spawnSync(process.execPath, ['--test', ...files], { stdio: 'inherit' });
process.exit(r.status ?? 1);
