import fs from "fs-extra";
import path from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";
import validateNpmPackageName from "validate-npm-package-name";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateProjectName(name: string): ValidationResult {
  const result = validateNpmPackageName(name);

  if (!result.validForNewPackages) {
    const errors = [...(result.errors || []), ...(result.warnings || [])];
    return {
      valid: false,
      error: errors[0] || "Invalid package name",
    };
  }

  return { valid: true };
}

export function getPackageVersion(): string {
  try {
    const packageJsonPath = path.resolve(__dirname, "..", "package.json");
    const packageJson = fs.readJsonSync(packageJsonPath);
    return packageJson.version || "0.0.0";
  } catch {
    return "0.0.0";
  }
}

export function getTemplateDir(): string {
  // In development, template is in the root template/ folder
  // In production (npm package), template is copied to dist/template/
  const devPath = path.resolve(__dirname, "..", "..", "..", "template");
  const prodPath = path.resolve(__dirname, "..", "template");

  if (fs.existsSync(devPath)) {
    return devPath;
  }
  return prodPath;
}

export async function copyTemplate(
  templateDir: string,
  targetDir: string,
  replacements: Record<string, string>,
): Promise<void> {
  await fs.copy(templateDir, targetDir);

  // Process template files (replace placeholders)
  const files = await getTemplateFiles(targetDir);

  for (const file of files) {
    if (file.endsWith(".template")) {
      const content = await fs.readFile(file, "utf-8");
      let processed = content;

      for (const [key, value] of Object.entries(replacements)) {
        processed = processed.replace(new RegExp(`{{${key}}}`, "g"), value);
      }

      const newPath = file.replace(".template", "");
      await fs.writeFile(newPath, processed);
      await fs.remove(file);
    }
  }
}

async function getTemplateFiles(dir: string): Promise<string[]> {
  const files: string[] = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await getTemplateFiles(fullPath)));
    } else {
      files.push(fullPath);
    }
  }

  return files;
}

export function initGit(dir: string): void {
  try {
    execSync("git init", { cwd: dir, stdio: "ignore" });
    execSync("git add -A", { cwd: dir, stdio: "ignore" });
    execSync('git commit -m "Initial commit from create-tether-app"', {
      cwd: dir,
      stdio: "ignore",
    });
  } catch {
    // Git init is optional, don't fail if it doesn't work
  }
}

export function installDependencies(
  dir: string,
  packageManager: "pnpm" | "npm" | "yarn",
): void {
  const commands: Record<string, string> = {
    pnpm: "pnpm install",
    npm: "npm install",
    yarn: "yarn",
  };

  execSync(commands[packageManager], {
    cwd: dir,
    stdio: "inherit",
  });
}

export function checkCommandExists(command: string): boolean {
  try {
    execSync(`which ${command}`, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}
