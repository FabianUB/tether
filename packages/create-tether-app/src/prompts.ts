import inquirer from "inquirer";

export interface PromptOptions {
  needsName: boolean;
}

export interface PromptAnswers {
  projectName: string;
  template: "local-llm" | "ollama" | "openai" | "gemini" | "custom";
  includeExample: boolean;
  useTailwind: boolean;
}

export async function promptForOptions(
  options: PromptOptions,
): Promise<PromptAnswers> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const questions: any[] = [];

  if (options.needsName) {
    questions.push({
      type: "input",
      name: "projectName",
      message: "Project name:",
      default: "my-tether-app",
      validate: (input: string) => {
        if (!input.trim()) {
          return "Project name is required";
        }
        if (!/^[a-z0-9-_]+$/i.test(input)) {
          return "Project name can only contain letters, numbers, hyphens, and underscores";
        }
        return true;
      },
    });
  }

  questions.push(
    {
      type: "list",
      name: "template",
      message: "Select model source:",
      choices: [
        {
          name: "Ollama - Run models locally via Ollama (Recommended)",
          value: "ollama",
        },
        {
          name: "Local LLM (llama-cpp-python) - Embed models directly",
          value: "local-llm",
        },
        {
          name: "OpenAI API - Use GPT models via API",
          value: "openai",
        },
        {
          name: "Google Gemini API - Use Gemini models via API",
          value: "gemini",
        },
        {
          name: "Custom - Bare FastAPI setup",
          value: "custom",
        },
      ],
      default: "ollama",
    },
    {
      type: "confirm",
      name: "includeExample",
      message: "Include example chat component?",
      default: true,
    },
    {
      type: "confirm",
      name: "useTailwind",
      message: "Add Tailwind CSS for styling?",
      default: false,
    },
  );

  const answers = await inquirer.prompt(questions);

  return {
    projectName: answers.projectName || "",
    template: answers.template || "ollama",
    includeExample: answers.includeExample ?? true,
    useTailwind: answers.useTailwind ?? false,
  };
}
