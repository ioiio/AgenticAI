using System.ClientModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;

namespace AI_Console;

public class SemKernel
{
    public static async Task GetSKResponse()
    {
        // Populate values from your OpenAI deployment
        var modelId = "Phi-4-mini-instruct";
        //var endpoint = "https://etdopenai.openai.azure.com/";
        //var apiKey = "";
        var uri = "https://models.inference.ai.azure.com";
        var githubPAT = Environment.GetEnvironmentVariable("GITHUB_TOKEN")??"";

        // Create a client to our GitHub Model
        var client = new OpenAIClient(new ApiKeyCredential(githubPAT), new OpenAIClientOptions
        {
            Endpoint = new Uri(uri)
        });

        // Create a kernel with Azure OpenAI chat completion
        //var builder = Kernel.CreateBuilder().AddOpenAIChatCompletion(modelId, client);

        // Create a kernel with OpenAI chat completion
        var builder = Kernel.CreateBuilder().AddOpenAIChatCompletion(modelId, client);

        // Add enterprise components
        builder.Services.AddLogging(services => services.AddConsole().SetMinimumLevel(LogLevel.Trace));

        // Build the kernel
        Kernel kernel = builder.Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Add a plugin (the LightsPlugin class is defined below)
        kernel.Plugins.AddFromType<LightsPlugin>("Lights");

        // Enable planning
        OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Create a history store the conversation
        var history = new ChatHistory();

        // Initiate a back-and-forth chat
        string? userInput;
        do {
            // Collect user input
            Console.Write("User > ");
            userInput = Console.ReadLine();

            // Add user input
            history.AddUserMessage(userInput?? "What is AI");

            // Get the response from the AI
            var result = await chatCompletionService.GetChatMessageContentAsync(
                history,
                executionSettings: openAIPromptExecutionSettings,
                kernel: kernel);

            // Print the results
            Console.WriteLine("Assistant > " + result);

            // Add the message from the agent to the chat history
            history.AddMessage(result.Role, result.Content ?? string.Empty);
        } while (userInput is not null);
    }
}