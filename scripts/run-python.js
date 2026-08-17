#!/usr/bin/env node
/* npm script가 운영체제별 Python launcher 차이와 무관하게 같은 인자를 실행하게 한다. */
'use strict';

const { spawnSync } = require('node:child_process');

const requested = process.env.PYTHON;
const candidates = requested
  ? [{ command: requested, prefix: [] }]
  : process.platform === 'win32'
    ? [
        { command: 'py', prefix: ['-3'] },
        { command: 'python', prefix: [] },
        { command: 'python3', prefix: [] },
      ]
    : [
        { command: 'python3', prefix: [] },
        { command: 'python', prefix: [] },
      ];

for (const candidate of candidates) {
  const result = spawnSync(candidate.command, [...candidate.prefix, ...process.argv.slice(2)], {
    stdio: 'inherit',
  });
  if (result.error && result.error.code === 'ENOENT') continue;
  if (result.error) {
    console.error(`Python 실행 실패 — ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.error('Python 3를 찾지 못하였다 — PYTHON 환경 변수 또는 python3·py·python 명령을 확인한다.');
process.exit(1);
