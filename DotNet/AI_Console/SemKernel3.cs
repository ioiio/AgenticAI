using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel;
using Microsoft.Extensions.Configuration;
using OpenAI;
using System.ClientModel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace AI_Console;

public class SemKernel3
{
    public static async Task GetSKResponse()
    {
        var githubToken = Environment.GetEnvironmentVariable("GITHUB_TOKEN");
        if (string.IsNullOrEmpty(githubToken))
        {
            var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();
            githubToken = config["GITHUB_TOKEN"]??"";
        }
        var modelId = "Phi-4-mini-instruct";
        var uri = "https://models.github.ai/inference";

        // create client
        var client = new OpenAIClient(new ApiKeyCredential(githubToken),new OpenAIClientOptions { Endpoint = new Uri(uri) });

        // Create a chat completion service
        var builder = Kernel.CreateBuilder();
        builder.Plugins.AddFromType<CityTemperaturePlugIn>();
        builder.AddOpenAIChatCompletion(modelId, client);

        // Get the chat completion service
        Kernel kernel = builder.Build();
        var chat = kernel.GetRequiredService<IChatCompletionService>();

        var history = new ChatHistory();
        history.AddSystemMessage("You are a useful chatbot. If you don't know an answer, say 'I don't know!'. Always reply in a funny way. Use emojis if possible.");

        while (true)
        {
            Console.Write("Q: ");
            var userQ = Console.ReadLine();
            if (string.IsNullOrEmpty(userQ))
            {
                break;
            }
            history.AddUserMessage(userQ);

            // Get the chat completions
            OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
            };
            var result = await chat.GetChatMessageContentAsync(history, executionSettings: openAIPromptExecutionSettings, kernel: kernel);
            Console.WriteLine($"AI: {result.Content}");
            history.AddAssistantMessage(result.Content ?? string.Empty);
            Console.WriteLine();
        }
    }
}