import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function getLocksDir() {
  // keep locks inside repo so it works across parallel projects/workers on same machine
  return path.resolve(__dirname, '../../playwright/.locks');
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Acquire a cross-process lock for E2E tests.
 * This prevents parallel Playwright projects from mutating shared backend state simultaneously.
 *
 * @param {string} name
 * @param {{ timeoutMs?: number, pollMs?: number }} [options]
 * @returns {Promise<() => Promise<void>>} release function
 */
export async function acquireE2ELock(name, options = {}) {
  const { timeoutMs = 120000, pollMs = 250 } = options;
  const dir = getLocksDir();
  const lockPath = path.join(dir, `${name}.lock`);
  const startedAt = Date.now();

  await fs.mkdir(dir, { recursive: true });

  // Retry until we can create the lock file exclusively.
  // Using 'wx' makes this atomic across processes.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const handle = await fs.open(lockPath, 'wx');
      try {
        await handle.writeFile(
          JSON.stringify(
            {
              pid: process.pid,
              created_at: new Date().toISOString(),
              name
            },
            null,
            2
          )
        );
      } finally {
        await handle.close();
      }

      let released = false;
      return async () => {
        if (released) return;
        released = true;
        await fs.unlink(lockPath).catch(() => {});
      };
    } catch (err) {
      if (err?.code !== 'EEXIST') throw err;
      if (Date.now() - startedAt > timeoutMs) {
        let holder = null;
        try {
          holder = await fs.readFile(lockPath, 'utf8');
        } catch {
          // ignored
        }
        throw new Error(
          `获取 E2E 锁超时: ${name}（等待 ${timeoutMs}ms）` +
            (holder ? `\n当前锁持有信息: ${holder}` : '')
        );
      }
      await sleep(pollMs);
    }
  }
}

