import { rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";

const rootDir = process.cwd();
const nextBin = path.join(rootDir, "node_modules", ".bin", process.platform === "win32" ? "next.cmd" : "next");
const windowsShell = process.env.ComSpec || "C:\\WINDOWS\\system32\\cmd.exe";

function cleanBuildDir() {
  rmSync(path.join(rootDir, ".next"), { recursive: true, force: true });
}

function runBuildAttempt(attempt) {
  cleanBuildDir();
  const result =
    process.platform === "win32"
      ? spawnSync(windowsShell, ["/c", nextBin, "build"], {
          cwd: rootDir,
          env: process.env,
          encoding: "utf-8",
        })
      : spawnSync(nextBin, ["build"], {
          cwd: rootDir,
          env: process.env,
          encoding: "utf-8",
        });

  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }

  if (result.status === 0) {
    return true;
  }

  if (attempt < 4) {
    process.stderr.write(
      `\n[WARN] next build fallo en el intento ${attempt}. Reintentando tras limpiar .next...\n`
    );
  }
  return false;
}

for (let attempt = 1; attempt <= 4; attempt += 1) {
  if (runBuildAttempt(attempt)) {
    process.exit(0);
  }
}

process.exit(1);
