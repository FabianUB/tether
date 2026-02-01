import fs from "fs-extra";
import path from "path";
import chalk from "chalk";
import ora from "ora";
import {
  getTemplateDir,
  copyTemplate,
  initGit,
  installDependencies,
  checkCommandExists,
} from "./utils.js";

export interface ScaffoldOptions {
  projectName: string;
  template: "local-llm" | "ollama" | "openai" | "custom";
  includeExample: boolean;
  skipInstall: boolean;
  packageManager: "pnpm" | "npm" | "yarn";
  useTailwind: boolean;
  verbose: boolean;
}

function log(message: string, verbose: boolean): void {
  if (verbose) {
    console.log(chalk.dim(`  ${message}`));
  }
}

export async function scaffoldProject(options: ScaffoldOptions): Promise<void> {
  const targetDir = path.resolve(process.cwd(), options.projectName);
  const { verbose } = options;

  // Check if directory already exists
  if (await fs.pathExists(targetDir)) {
    throw new Error(
      `Directory "${options.projectName}" already exists. Please choose a different name.`,
    );
  }

  // Check for required tools
  const spinner = ora("Checking prerequisites...").start();

  if (!checkCommandExists("uv")) {
    spinner.warn(
      chalk.yellow("uv not found. Install it from https://docs.astral.sh/uv/"),
    );
    console.log(
      chalk.dim(
        "  You can still create the project, but Python setup may fail.",
      ),
    );
    console.log();
  }

  if (options.packageManager === "pnpm" && !checkCommandExists("pnpm")) {
    spinner.warn(chalk.yellow("pnpm not found. Falling back to npm."));
    options.packageManager = "npm";
  }

  spinner.succeed("Prerequisites checked");

  // Copy template
  spinner.start("Creating project structure...");
  log(`Target directory: ${targetDir}`, verbose);

  const templateDir = getTemplateDir();
  log(`Template directory: ${templateDir}`, verbose);

  if (!(await fs.pathExists(templateDir))) {
    spinner.fail("Template directory not found");
    throw new Error(
      "Template directory not found. This may be a bug in create-tether-app.",
    );
  }

  try {
    await fs.ensureDir(targetDir);
  } catch (error) {
    if (error instanceof Error && error.message.includes("EACCES")) {
      throw new Error(
        `Permission denied creating directory "${options.projectName}". Check your permissions.`,
      );
    }
    throw error;
  }

  await copyTemplate(templateDir, targetDir, {
    PROJECT_NAME: options.projectName,
    TEMPLATE: options.template,
  });
  log("Template files copied", verbose);

  // Customize based on template choice
  await customizeForTemplate(targetDir, options);
  log(`Configured for ${options.template} backend`, verbose);

  spinner.succeed("Project structure created");

  // Setup Tailwind if requested, otherwise remove template files
  if (options.useTailwind) {
    spinner.start("Setting up Tailwind CSS...");
    await setupTailwind(targetDir, verbose);
    spinner.succeed("Tailwind CSS configured");
  } else {
    // Remove Tailwind template files that were copied
    await removeTailwindTemplateFiles(targetDir, verbose);
  }

  // Remove example if not wanted
  if (!options.includeExample) {
    spinner.start("Removing example components...");
    await removeExampleComponents(targetDir);
    spinner.succeed("Example components removed");
  }

  // Initialize git
  spinner.start("Initializing git repository...");
  initGit(targetDir);
  spinner.succeed("Git repository initialized");

  // Install dependencies
  if (!options.skipInstall) {
    spinner.start(`Installing dependencies with ${options.packageManager}...`);
    try {
      installDependencies(targetDir, options.packageManager);
      spinner.succeed("Dependencies installed");
    } catch (error) {
      spinner.fail("Failed to install dependencies");
      console.log(chalk.yellow("  You can install them manually later."));
      if (verbose && error instanceof Error) {
        console.log(chalk.dim(`  Error: ${error.message}`));
      }
    }
  }

  // Print success message
  console.log();
  console.log(chalk.green.bold("  Success!"), `Created ${options.projectName}`);
  console.log();
  console.log("  Next steps:");
  console.log();
  console.log(chalk.cyan(`    cd ${options.projectName}`));

  if (options.skipInstall) {
    console.log(chalk.cyan(`    ${options.packageManager} install`));
  }

  console.log(chalk.cyan("    pnpm dev          # Start frontend"));
  console.log(chalk.cyan("    pnpm dev:py       # Start Python backend"));
  console.log(chalk.cyan("    pnpm dev:all      # Start both"));
  console.log();
  console.log("  To build the desktop app:");
  console.log();
  console.log(chalk.cyan("    pnpm build:app"));
  console.log();

  if (options.template === "ollama") {
    console.log(
      chalk.dim("  Note: Make sure Ollama is running (ollama serve)."),
    );
    console.log(chalk.dim("  Pull a model with: ollama pull llama3.2"));
    console.log();
  } else if (options.template === "local-llm") {
    console.log(
      chalk.dim(
        "  Note: For local LLM support, you'll need to download a model.",
      ),
    );
    console.log(
      chalk.dim("  See the README.md in your project for instructions."),
    );
    console.log();
  } else if (options.template === "openai") {
    console.log(
      chalk.dim(
        "  Note: Set your OPENAI_API_KEY in .env to use the OpenAI API.",
      ),
    );
    console.log();
  }

  if (options.useTailwind) {
    console.log(
      chalk.dim("  Tailwind CSS is configured. Use utility classes in your components."),
    );
    console.log();
  }
}

async function setupTailwind(targetDir: string, verbose: boolean): Promise<void> {
  const templateDir = getTemplateDir();

  // Copy tailwind.config.js (remove .template extension)
  const tailwindTemplatePath = path.join(templateDir, "tailwind.config.js.template");
  const tailwindTargetPath = path.join(targetDir, "tailwind.config.js");

  if (await fs.pathExists(tailwindTemplatePath)) {
    await fs.copy(tailwindTemplatePath, tailwindTargetPath);
    log("Created tailwind.config.js", verbose);
  }

  // Copy postcss.config.js (remove .template extension)
  const postcssTemplatePath = path.join(templateDir, "postcss.config.js.template");
  const postcssTargetPath = path.join(targetDir, "postcss.config.js");

  if (await fs.pathExists(postcssTemplatePath)) {
    await fs.copy(postcssTemplatePath, postcssTargetPath);
    log("Created postcss.config.js", verbose);
  }

  // Prepend Tailwind directives to index.css
  const indexCssPath = path.join(targetDir, "frontend", "index.css");
  if (await fs.pathExists(indexCssPath)) {
    const existingCss = await fs.readFile(indexCssPath, "utf-8");
    const tailwindDirectives = `@tailwind base;
@tailwind components;
@tailwind utilities;

`;
    await fs.writeFile(indexCssPath, tailwindDirectives + existingCss);
    log("Added Tailwind directives to index.css", verbose);
  }

  // Add Tailwind dependencies to package.json
  const packageJsonPath = path.join(targetDir, "package.json");
  if (await fs.pathExists(packageJsonPath)) {
    const packageJson = await fs.readJson(packageJsonPath);

    packageJson.devDependencies = packageJson.devDependencies || {};
    packageJson.devDependencies["tailwindcss"] = "^3.4.0";
    packageJson.devDependencies["postcss"] = "^8.4.0";
    packageJson.devDependencies["autoprefixer"] = "^10.4.0";

    await fs.writeJson(packageJsonPath, packageJson, { spaces: 2 });
    log("Added Tailwind dependencies to package.json", verbose);
  }
}

async function customizeForTemplate(
  targetDir: string,
  options: ScaffoldOptions,
): Promise<void> {
  const pythonServicePath = path.join(
    targetDir,
    "backend",
    "app",
    "services",
    "llm.py",
  );

  // Adjust Python dependencies based on template
  const pyprojectPath = path.join(targetDir, "backend", "pyproject.toml");
  if (await fs.pathExists(pyprojectPath)) {
    let content = await fs.readFile(pyprojectPath, "utf-8");

    if (options.template === "ollama") {
      // Remove llama-cpp-python, keep httpx for ollama
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, "");
      content = content.replace(/^\s*"openai[^"]*",?\n/gm, "");
    } else if (options.template === "openai") {
      // Remove llama-cpp-python, keep openai
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, "");
    } else if (options.template === "custom") {
      // Remove all LLM dependencies
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, "");
      content = content.replace(/^\s*"openai[^"]*",?\n/gm, "");
    }

    await fs.writeFile(pyprojectPath, content);
  }

  // Adjust the LLM service based on template
  if (await fs.pathExists(pythonServicePath)) {
    let content = await fs.readFile(pythonServicePath, "utf-8");

    // Match tether_llm_backend: Literal[...] = "any_value"
    const backendRegex =
      /(tether_llm_backend:\s*Literal\[[^\]]+\]\s*=\s*)["'][^"']+["']/;

    if (options.template === "local-llm") {
      content = content.replace(backendRegex, '$1"local"');
    } else if (options.template === "ollama") {
      content = content.replace(backendRegex, '$1"ollama"');
    } else if (options.template === "openai") {
      content = content.replace(backendRegex, '$1"openai"');
    } else if (options.template === "custom") {
      content = content.replace(backendRegex, '$1"mock"');
    }

    await fs.writeFile(pythonServicePath, content);
  }
}

async function removeTailwindTemplateFiles(targetDir: string, verbose: boolean): Promise<void> {
  const tailwindConfigPath = path.join(targetDir, "tailwind.config.js");
  const postcssConfigPath = path.join(targetDir, "postcss.config.js");

  if (await fs.pathExists(tailwindConfigPath)) {
    await fs.remove(tailwindConfigPath);
    log("Removed tailwind.config.js (not requested)", verbose);
  }

  if (await fs.pathExists(postcssConfigPath)) {
    await fs.remove(postcssConfigPath);
    log("Removed postcss.config.js (not requested)", verbose);
  }
}

async function removeExampleComponents(targetDir: string): Promise<void> {
  const exampleFiles = [
    path.join(targetDir, "frontend", "components", "Chat.tsx"),
    path.join(targetDir, "frontend", "components", "ChatMessage.tsx"),
  ];

  for (const file of exampleFiles) {
    if (await fs.pathExists(file)) {
      await fs.remove(file);
    }
  }

  // Update App.tsx to remove Chat import
  const appPath = path.join(targetDir, "frontend", "App.tsx");
  if (await fs.pathExists(appPath)) {
    let content = await fs.readFile(appPath, "utf-8");
    content = content.replace(/import.*Chat.*from.*\n?/g, "");
    content = content.replace(/<Chat\s*\/>/g, "");
    await fs.writeFile(appPath, content);
  }
}
