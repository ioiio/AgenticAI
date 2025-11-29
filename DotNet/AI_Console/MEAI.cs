using Azure;
using Azure.AI.Inference;
using Microsoft.Extensions.AI;

namespace AI_Console;

public class MEAI
{
    public static async Task GetMEAIResponse()
    {
        IChatClient client = new ChatCompletionsClient(
        //endpoint: new Uri("https://models.github.ai/inference"),
        endpoint: new Uri("https://models.inference.ai.azure.com/"),
        new AzureKeyCredential(Environment.GetEnvironmentVariable("GITHUB_TOKEN") ?? throw new InvalidOperationException("Missing GITHUB_TOKEN environment variable. Ensure you followed the instructions to setup a GitHub Token to use GitHub Models.")))
        .AsIChatClient("Phi-4-mini-instruct");

        var response = await client.GetResponseAsync("What is AI?");

        Console.WriteLine(response.Text);
    }
}
