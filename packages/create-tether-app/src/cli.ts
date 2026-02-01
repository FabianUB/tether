import { Command } from "commander";
import { scaffoldProject } from "./scaffold.js";
import { promptForOptions } from "./prompts.js";
import {
  validateProjectName,
  getPackageVersion,
  checkEnvironment,
} from "./utils.js";
import chalk from "chalk";

export interface CliOptions {
  llm?: "ollama" | "local-llm" | "openai" | "custom";
  template?: "ollama" | "local-llm" | "openai" | "custom"; // alias for --llm
  yes?: boolean;
  skipPrompts?: boolean; // alias for --yes
  skipInstall?: boolean;
  useNpm?: boolean;
  useYarn?: boolean;
  dryRun?: boolean;
  example?: boolean; // --no-example sets this to false
  tailwind?: boolean; // --tailwind or --no-tailwind
  verbose?: boolean;
  listTemplates?: boolean;
  check?: boolean;
}

const LLM_TEMPLATES = [
  {
    name: "ollama",
    description: "Run models locally via Ollama (Recommended)",
    details:
      "Requires Ollama to be installed and running. Pull models with 'ollama pull'.",
  },
  {
    name: "local-llm",
    description: "Embed models directly with llama-cpp-python",
    details: "Models are bundled with the app. Good for offline distribution.",
  },
  {
    name: "openai",
    description: "Use OpenAI API (requires API key)",
    details:
      "Uses GPT models via the OpenAI API. Requires OPENAI_API_KEY env var.",
  },
  {
    name: "custom",
    description: "Bare FastAPI setup, no LLM integration",
    details: "Clean slate for custom ML/AI implementations.",
  },
];

export function createCli(): Command {
  const program = new Command();

  program
    .name("create-tether-app")
    .description("Create a new Tether AI/ML desktop application")
    .version(getPackageVersion())
    .argument("[project-name]", "Name of the project to create")
    .option(
      "--llm <provider>",
      "LLM backend: ollama (default), local-llm, openai, custom",
    )
    .option("-t, --template <template>", "Alias for --llm")
    .option("-y, --yes", "Skip prompts and use defaults (ollama, with example)")
    .option("--skip-prompts", "Alias for --yes")
    .option("--skip-install", "Skip dependency installation")
    .option("--use-npm", "Use npm instead of pnpm")
    .option("--use-yarn", "Use yarn instead of pnpm")
    .option("--dry-run", "Show what would be created without making changes")
    .option("--no-example", "Skip example chat component")
    .option("--tailwind", "Include Tailwind CSS setup")
    .option("--no-tailwind", "Skip Tailwind CSS setup")
    .option("-v, --verbose", "Show detailed output")
    .option("--list-templates", "List available LLM templates")
    .option("--check", "Check if all required dependencies are installed")
    .addHelpText(
      "after",
      `
Examples:
  ${chalk.cyan("npx create-tether-app my-app")}
    Create a new app with interactive prompts

  ${chalk.cyan("npx create-tether-app my-app -y")}
    Create with defaults (ollama, includes example)

  ${chalk.cyan("npx create-tether-app my-app --llm openai")}
    Create with OpenAI backend

  ${chalk.cyan("npx create-tether-app my-app --tailwind")}
    Create with Tailwind CSS support

  ${chalk.cyan("npx create-tether-app my-app --dry-run")}
    Preview what would be created

  ${chalk.cyan("npx create-tether-app --list-templates")}
    Show available LLM backends

  ${chalk.cyan("npx create-tether-app --check")}
    Check if all dependencies are installed

LLM Backends:
  ollama      Run models locally via Ollama (recommended)
  local-llm   Embed models directly with llama-cpp-python
  openai      Use OpenAI API (requires API key)
  custom      Bare FastAPI setup, no LLM integration
`,
    )
    .action(async (projectName: string | undefined, options: CliOptions) => {
      // Handle --list-templates
      if (options.listTemplates) {
        console.log();
        console.log(chalk.bold("Available LLM Templates:"));
        console.log();
        for (const template of LLM_TEMPLATES) {
          console.log(chalk.cyan(`  ${template.name}`));
          console.log(chalk.white(`    ${template.description}`));
          console.log(chalk.dim(`    ${template.details}`));
          console.log();
        }
        return;
      }

      // Handle --check
      if (options.check) {
        console.log();
        console.log(chalk.bold("Checking dependencies..."));
        console.log();
        const checks = checkEnvironment();
        let allGood = true;

        for (const dep of checks) {
          const status = dep.installed
            ? chalk.green("✓")
            : dep.required === "optional"
              ? chalk.yellow("○")
              : chalk.red("✗");
          const version = dep.version ? chalk.dim(` (${dep.version})`) : "";
          const required =
            dep.required === "optional"
              ? chalk.dim(" [optional]")
              : chalk.dim(` [${dep.required}]`);

          console.log(`  ${status} ${dep.name}${version}${required}`);

          if (!dep.installed && dep.required !== "optional") {
            allGood = false;
            console.log(chalk.dim(`      Install: ${dep.installUrl}`));
          }
        }

        console.log();
        if (allGood) {
          console.log(chalk.green("All required dependencies are installed!"));
        } else {
          console.log(
            chalk.yellow(
              "Some dependencies are missing. Install them before creating a project.",
            ),
          );
        }
        console.log();
        return;
      }

      console.log();
      console.log(chalk.bold.cyan("  Tether"));
      console.log(chalk.dim("  Create AI/ML desktop applications"));
      console.log();

      // Run dependency check and warn about missing deps
      const checks = checkEnvironment();
      const missing = checks.filter(
        (d) => !d.installed && d.required !== "optional",
      );
      if (missing.length > 0) {
        console.log(chalk.yellow("Warning: Some dependencies are missing:"));
        for (const dep of missing) {
          console.log(chalk.yellow(`  - ${dep.name}: ${dep.installUrl}`));
        }
        console.log();
      }

      try {
        // Handle aliases
        const llmProvider = options.llm || options.template;
        const skipPrompts = options.yes || options.skipPrompts;
        const verbose = options.verbose || false;

        // Validate or prompt for project name
        let name = projectName;
        if (!name) {
          if (skipPrompts || options.dryRun) {
            console.error(chalk.red("Error: Project name is required"));
            console.log(
              chalk.dim("  Usage: npx create-tether-app my-app [options]"),
            );
            process.exit(1);
          }
          const answers = await promptForOptions({ needsName: true });
          name = answers.projectName;
        }

        const validation = validateProjectName(name);
        if (!validation.valid) {
          console.error(chalk.red(`Error: Invalid project name "${name}"`));
          console.log(chalk.dim(`  ${validation.error}`));
          console.log(
            chalk.dim(
              "  Project names must be lowercase and can contain letters, numbers, and hyphens.",
            ),
          );
          process.exit(1);
        }

        // Get template options
        let template = llmProvider;
        let includeExample = options.example !== false;
        let useTailwind = options.tailwind;

        // For dry-run and --yes/--skip-prompts, skip prompts and use defaults
        if (!skipPrompts && !options.dryRun && !template) {
          const answers = await promptForOptions({ needsName: false });
          template = answers.template;
          includeExample = answers.includeExample;
          // Only prompt for tailwind if not explicitly set via flag
          if (useTailwind === undefined) {
            useTailwind = answers.useTailwind;
          }
        }

        // Default to ollama if not specified
        template = template || "ollama";
        // Default to no tailwind if not specified (for --yes and --dry-run)
        useTailwind = useTailwind ?? false;

        // Dry run mode - show what would be created
        if (options.dryRun) {
          console.log(chalk.yellow("Dry run mode - no changes will be made"));
          console.log();
          console.log("Would create project:");
          console.log(chalk.cyan(`  Name: ${name}`));
          console.log(chalk.cyan(`  LLM Backend: ${template}`));
          console.log(
            chalk.cyan(`  Include Example: ${includeExample ? "yes" : "no"}`),
          );
          console.log(
            chalk.cyan(`  Tailwind CSS: ${useTailwind ? "yes" : "no"}`),
          );
          console.log(
            chalk.cyan(
              `  Package Manager: ${options.useNpm ? "npm" : options.useYarn ? "yarn" : "pnpm"}`,
            ),
          );
          console.log();
          console.log("Would create directory structure:");
          console.log(chalk.dim(`  ${name}/`));
          console.log(
            chalk.dim(`  ├── frontend/          # React + TypeScript + Vite`),
          );
          console.log(chalk.dim(`  ├── backend/           # Python + FastAPI`));
          console.log(chalk.dim(`  └── src-tauri/         # Tauri (Rust)`));
          if (useTailwind) {
            console.log();
            console.log("Tailwind files:");
            console.log(chalk.dim(`  ├── tailwind.config.js`));
            console.log(chalk.dim(`  └── postcss.config.js`));
          }
          console.log();
          console.log("Would install dependencies:");
          console.log(
            chalk.dim(
              `  react, react-dom, vite, typescript, @tauri-apps/cli, ...`,
            ),
          );
          if (useTailwind) {
            console.log(chalk.dim(`  tailwindcss, postcss, autoprefixer`));
          }
          console.log();
          return;
        }

        // Scaffold the project
        await scaffoldProject({
          projectName: name,
          template: template as "local-llm" | "ollama" | "openai" | "custom",
          includeExample,
          skipInstall: options.skipInstall || false,
          packageManager: options.useNpm
            ? "npm"
            : options.useYarn
              ? "yarn"
              : "pnpm",
          useTailwind,
          verbose,
        });
      } catch (error) {
        if (error instanceof Error) {
          console.error(chalk.red(`Error: ${error.message}`));

          // Provide helpful suggestions for common errors
          if (error.message.includes("already exists")) {
            console.log(
              chalk.dim(
                "  Try a different project name or delete the existing directory.",
              ),
            );
          } else if (
            error.message.includes("EACCES") ||
            error.message.includes("permission")
          ) {
            console.log(
              chalk.dim(
                "  Permission denied. Try running with sudo or check directory permissions.",
              ),
            );
          } else if (
            error.message.includes("uv not found") ||
            error.message.includes("uv")
          ) {
            console.log(
              chalk.dim(
                "  Install uv from: https://docs.astral.sh/uv/getting-started/installation/",
              ),
            );
          }
        }
        process.exit(1);
      }
    });

  return program;
}
