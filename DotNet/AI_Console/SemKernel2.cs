using System.ClientModel;
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;

namespace AI_Console;

public class SemKernel2
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

        // // Create a kernel with Azure OpenAI chat completion
        // var builder = Kernel.CreateBuilder().AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);

        // Create a kernel with OpenAI chat completion
        var builder = Kernel.CreateBuilder().AddOpenAIChatCompletion(modelId, client);
       
        // Build the kernel
        Kernel kernel = builder.Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var history = new ChatHistory();
        history.AddSystemMessage("You are a useful gym chatbot. You will limit your answers to purely gym-related topics. Any other topics, " +
        "or you don't know an answer, say 'I'm sorry, I can't help with that!'");

        while (true)
        {
            Console.Write("Q: ");
            var userQ = Console.ReadLine();
            if (string.IsNullOrEmpty(userQ))
            {
                break;
            }
            history.AddUserMessage(userQ);

            var sb = new StringBuilder();
            var result = chatCompletionService.GetStreamingChatMessageContentsAsync(history);
            Console.Write("AI: ");
            await foreach (var item in result)
            {
                sb.Append(item);
                Console.Write(item.Content);
            }
            Console.WriteLine();

            history.AddAssistantMessage(sb.ToString());
        }
    }
}