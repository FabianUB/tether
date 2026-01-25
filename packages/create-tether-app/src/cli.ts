import { Command } from 'commander';
import { scaffoldProject } from './scaffold.js';
import { promptForOptions } from './prompts.js';
import { validateProjectName, getPackageVersion } from './utils.js';
import chalk from 'chalk';

export interface CliOptions {
  template?: 'local-llm' | 'openai' | 'custom';
  skipPrompts?: boolean;
  skipInstall?: boolean;
  useNpm?: boolean;
  useYarn?: boolean;
}

export function createCli(): Command {
  const program = new Command();

  program
    .name('create-tether-app')
    .description('Create a new Tether AI/ML desktop application')
    .version(getPackageVersion())
    .argument('[project-name]', 'Name of the project to create')
    .option('-t, --template <template>', 'ML backend template (local-llm, openai, custom)')
    .option('--skip-prompts', 'Skip interactive prompts and use defaults')
    .option('--skip-install', 'Skip dependency installation')
    .option('--use-npm', 'Use npm instead of pnpm')
    .option('--use-yarn', 'Use yarn instead of pnpm')
    .action(async (projectName: string | undefined, options: CliOptions) => {
      console.log();
      console.log(chalk.bold.cyan('  Tether'));
      console.log(chalk.dim('  Create AI/ML desktop applications'));
      console.log();

      try {
        // Validate or prompt for project name
        let name = projectName;
        if (!name) {
          const answers = await promptForOptions({ needsName: true });
          name = answers.projectName;
        }

        const validation = validateProjectName(name);
        if (!validation.valid) {
          console.error(chalk.red(`Invalid project name: ${validation.error}`));
          process.exit(1);
        }

        // Get template options
        let template = options.template;
        let includeExample = true;

        if (!options.skipPrompts && !template) {
          const answers = await promptForOptions({ needsName: false });
          template = answers.template;
          includeExample = answers.includeExample;
        }

        // Default to local-llm if not specified
        template = template || 'local-llm';

        // Scaffold the project
        await scaffoldProject({
          projectName: name,
          template: template as 'local-llm' | 'openai' | 'custom',
          includeExample,
          skipInstall: options.skipInstall || false,
          packageManager: options.useNpm ? 'npm' : options.useYarn ? 'yarn' : 'pnpm',
        });
      } catch (error) {
        if (error instanceof Error) {
          console.error(chalk.red(`Error: ${error.message}`));
        }
        process.exit(1);
      }
    });

  return program;
}
