using System.ClientModel;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using OpenAI;
using OpenAI.Chat;

class AgentFx
{
    public static async Task GetAIResponse()
    {
        var githubToken = Environment.GetEnvironmentVariable("GITHUB_TOKEN");
        if (string.IsNullOrEmpty(githubToken))
        {
            var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();
            githubToken = config["GITHUB_TOKEN"];
        }

        IChatClient chatClient =
            new ChatClient(
                    "gpt-4o-mini",
                    new ApiKeyCredential(githubToken!),
                    new OpenAIClientOptions { Endpoint = new Uri("https://models.github.ai/inference") })
                .AsIChatClient();

        AIAgent writer = new ChatClientAgent(
            chatClient,
            new ChatClientAgentOptions
            {
                Name = "Writer",
                //Instructions = "Write stories that are engaging and creative."
            });

        AgentRunResponse response = await writer.RunAsync("Write a short story about life of Osho");

        Console.WriteLine(response.Text);
    }
}