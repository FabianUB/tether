import { Command } from "commander";
import { scaffoldProject } from "./scaffold.js";
import { promptForOptions } from "./prompts.js";
import { validateProjectName, getPackageVersion } from "./utils.js";
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
}

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

  ${chalk.cyan("npx create-tether-app my-app --dry-run")}
    Preview what would be created

LLM Backends:
  ollama      Run models locally via Ollama (recommended)
  local-llm   Embed models directly with llama-cpp-python
  openai      Use OpenAI API (requires API key)
  custom      Bare FastAPI setup, no LLM integration
`,
    )
    .action(async (projectName: string | undefined, options: CliOptions) => {
      console.log();
      console.log(chalk.bold.cyan("  Tether"));
      console.log(chalk.dim("  Create AI/ML desktop applications"));
      console.log();

      try {
        // Handle aliases
        const llmProvider = options.llm || options.template;
        const skipPrompts = options.yes || options.skipPrompts;

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

        // For dry-run and --yes/--skip-prompts, skip prompts and use defaults
        if (!skipPrompts && !options.dryRun && !template) {
          const answers = await promptForOptions({ needsName: false });
          template = answers.template;
          includeExample = answers.includeExample;
        }

        // Default to ollama if not specified
        template = template || "ollama";

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
          }
        }
        process.exit(1);
      }
    });

  return program;
}
