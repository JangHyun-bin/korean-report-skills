// korean-report-skills — OpenCode plugin.
//
// Registers the two skills (korean-report-doc, korean-report-style) so they load
// when this package is added to opencode.json:
//   { "plugin": ["korean-report-skills"] }
//
// OpenCode loads this as a server plugin; the config hook appends the skills
// directory to config.skills.paths so the skill loader scans it.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsDir = path.resolve(__dirname, '..', '..', 'plugins', 'korean-report', 'skills');

export default async () => {
  if (!fs.existsSync(skillsDir)) {
    return {};
  }

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },
  };
};
