import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import {
  getTemplateDir,
  copyTemplate,
  initGit,
  installDependencies,
  checkCommandExists,
} from './utils.js';

export interface ScaffoldOptions {
  projectName: string;
  template: 'local-llm' | 'ollama' | 'openai' | 'custom';
  includeExample: boolean;
  skipInstall: boolean;
  packageManager: 'pnpm' | 'npm' | 'yarn';
}

export async function scaffoldProject(options: ScaffoldOptions): Promise<void> {
  const targetDir = path.resolve(process.cwd(), options.projectName);

  // Check if directory already exists
  if (await fs.pathExists(targetDir)) {
    throw new Error(
      `Directory "${options.projectName}" already exists. Please choose a different name.`
    );
  }

  // Check for required tools
  const spinner = ora('Checking prerequisites...').start();

  if (!checkCommandExists('uv')) {
    spinner.warn(
      chalk.yellow('uv not found. Install it from https://docs.astral.sh/uv/')
    );
    console.log(
      chalk.dim('  You can still create the project, but Python setup may fail.')
    );
    console.log();
  }

  if (options.packageManager === 'pnpm' && !checkCommandExists('pnpm')) {
    spinner.warn(
      chalk.yellow('pnpm not found. Falling back to npm.')
    );
    options.packageManager = 'npm';
  }

  spinner.succeed('Prerequisites checked');

  // Copy template
  spinner.start('Creating project structure...');

  const templateDir = getTemplateDir();

  if (!(await fs.pathExists(templateDir))) {
    spinner.fail('Template directory not found');
    throw new Error(
      'Template directory not found. This may be a bug in create-tether-app.'
    );
  }

  await fs.ensureDir(targetDir);
  await copyTemplate(templateDir, targetDir, {
    PROJECT_NAME: options.projectName,
    TEMPLATE: options.template,
  });

  // Customize based on template choice
  await customizeForTemplate(targetDir, options);

  spinner.succeed('Project structure created');

  // Remove example if not wanted
  if (!options.includeExample) {
    spinner.start('Removing example components...');
    await removeExampleComponents(targetDir);
    spinner.succeed('Example components removed');
  }

  // Initialize git
  spinner.start('Initializing git repository...');
  initGit(targetDir);
  spinner.succeed('Git repository initialized');

  // Install dependencies
  if (!options.skipInstall) {
    spinner.start(`Installing dependencies with ${options.packageManager}...`);
    try {
      installDependencies(targetDir, options.packageManager);
      spinner.succeed('Dependencies installed');
    } catch (error) {
      spinner.fail('Failed to install dependencies');
      console.log(chalk.yellow('  You can install them manually later.'));
    }
  }

  // Print success message
  console.log();
  console.log(chalk.green.bold('  Success!'), `Created ${options.projectName}`);
  console.log();
  console.log('  Next steps:');
  console.log();
  console.log(chalk.cyan(`    cd ${options.projectName}`));

  if (options.skipInstall) {
    console.log(chalk.cyan(`    ${options.packageManager} install`));
  }

  console.log(chalk.cyan('    pnpm dev'));
  console.log();
  console.log('  To build for production:');
  console.log();
  console.log(chalk.cyan('    pnpm build'));
  console.log();

  if (options.template === 'ollama') {
    console.log(chalk.dim('  Note: Make sure Ollama is running (ollama serve).'));
    console.log(chalk.dim('  Pull a model with: ollama pull llama3.2'));
    console.log();
  } else if (options.template === 'local-llm') {
    console.log(chalk.dim('  Note: For local LLM support, you\'ll need to download a model.'));
    console.log(chalk.dim('  See the README.md in your project for instructions.'));
    console.log();
  } else if (options.template === 'openai') {
    console.log(chalk.dim('  Note: Set your OPENAI_API_KEY in .env to use the OpenAI API.'));
    console.log();
  }
}

async function customizeForTemplate(
  targetDir: string,
  options: ScaffoldOptions
): Promise<void> {
  const pythonServicePath = path.join(
    targetDir,
    'backend',
    'app',
    'services',
    'llm.py'
  );

  // Adjust Python dependencies based on template
  const pyprojectPath = path.join(targetDir, 'backend', 'pyproject.toml');
  if (await fs.pathExists(pyprojectPath)) {
    let content = await fs.readFile(pyprojectPath, 'utf-8');

    if (options.template === 'ollama') {
      // Remove llama-cpp-python, keep httpx for ollama
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, '');
      content = content.replace(/^\s*"openai[^"]*",?\n/gm, '');
    } else if (options.template === 'openai') {
      // Remove llama-cpp-python, keep openai
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, '');
    } else if (options.template === 'custom') {
      // Remove all LLM dependencies
      content = content.replace(/^\s*"llama-cpp-python[^"]*",?\n/gm, '');
      content = content.replace(/^\s*"openai[^"]*",?\n/gm, '');
    }

    await fs.writeFile(pyprojectPath, content);
  }

  // Adjust the LLM service based on template
  if (await fs.pathExists(pythonServicePath)) {
    let content = await fs.readFile(pythonServicePath, 'utf-8');

    // The template uses: tether_llm_backend: Literal[...] = "local"
    const backendRegex = /(tether_llm_backend:\s*Literal\[[^\]]+\]\s*=\s*)["']local["']/;

    if (options.template === 'ollama') {
      content = content.replace(backendRegex, '$1"ollama"');
    } else if (options.template === 'openai') {
      content = content.replace(backendRegex, '$1"openai"');
    } else if (options.template === 'custom') {
      content = content.replace(backendRegex, '$1"mock"');
    }

    await fs.writeFile(pythonServicePath, content);
  }
}

async function removeExampleComponents(targetDir: string): Promise<void> {
  const exampleFiles = [
    path.join(targetDir, 'frontend', 'components', 'Chat.tsx'),
    path.join(targetDir, 'frontend', 'components', 'ChatMessage.tsx'),
  ];

  for (const file of exampleFiles) {
    if (await fs.pathExists(file)) {
      await fs.remove(file);
    }
  }

  // Update App.tsx to remove Chat import
  const appPath = path.join(targetDir, 'frontend', 'App.tsx');
  if (await fs.pathExists(appPath)) {
    let content = await fs.readFile(appPath, 'utf-8');
    content = content.replace(/import.*Chat.*from.*\n?/g, '');
    content = content.replace(/<Chat\s*\/>/g, '');
    await fs.writeFile(appPath, content);
  }
}
