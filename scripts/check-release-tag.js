#!/usr/bin/env node
/* Git tag와 package.json version이 같은 릴리스를 가리키는지 확인한다. */
'use strict';

const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const pkg = require(path.join(ROOT, 'package.json'));
const tag = process.argv[2] || process.env.GITHUB_REF_NAME || '';
const expected = `v${pkg.version}`;

if (!tag) {
  console.error('릴리스 tag가 없다 — 인자 또는 GITHUB_REF_NAME으로 전달한다.');
  process.exit(1);
}

if (tag !== expected) {
  console.error(`릴리스 tag와 package version이 어긋난다 — tag ${tag} · expected ${expected}`);
  process.exit(1);
}

console.log(`릴리스 tag 확인 — ${tag}`);
