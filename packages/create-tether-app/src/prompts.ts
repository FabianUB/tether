import inquirer from 'inquirer';

export interface PromptOptions {
  needsName: boolean;
}

export interface PromptAnswers {
  projectName: string;
  template: 'local-llm' | 'openai' | 'custom';
  includeExample: boolean;
}

export async function promptForOptions(
  options: PromptOptions
): Promise<PromptAnswers> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const questions: any[] = [];

  if (options.needsName) {
    questions.push({
      type: 'input',
      name: 'projectName',
      message: 'Project name:',
      default: 'my-tether-app',
      validate: (input: string) => {
        if (!input.trim()) {
          return 'Project name is required';
        }
        if (!/^[a-z0-9-_]+$/i.test(input)) {
          return 'Project name can only contain letters, numbers, hyphens, and underscores';
        }
        return true;
      },
    });
  }

  questions.push(
    {
      type: 'list',
      name: 'template',
      message: 'Select ML backend:',
      choices: [
        {
          name: 'Local LLM (llama-cpp-python) - Run models locally',
          value: 'local-llm',
        },
        {
          name: 'OpenAI API - Use GPT models via API',
          value: 'openai',
        },
        {
          name: 'Custom - Bare FastAPI setup',
          value: 'custom',
        },
      ],
      default: 'local-llm',
    },
    {
      type: 'confirm',
      name: 'includeExample',
      message: 'Include example chat component?',
      default: true,
    }
  );

  const answers = await inquirer.prompt(questions);

  return {
    projectName: answers.projectName || '',
    template: answers.template || 'local-llm',
    includeExample: answers.includeExample ?? true,
  };
}
