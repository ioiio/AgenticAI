using System.ClientModel;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using OpenAI;
using OpenAI.Chat;

class AgentFx_MultiModel
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

        string prompt = "Write a short story about life of Osho";
        AgentRunResponse response = await writer.RunAsync(prompt);
        Console.WriteLine(response.Text);

        // Create a specialized editor agent
        AIAgent editor = new ChatClientAgent(
            chatClient,
            new ChatClientAgentOptions
            {
                Name = "Editor",
                //Instructions = "Make the story more engaging, fix grammar, and enhance the plot."
            });

        // Create a workflow that connects writer to editor
        Workflow workflow = AgentWorkflowBuilder.BuildSequential(writer, editor);

        AIAgent workflowAgent = workflow.AsAgent();

        AgentRunResponse workflowResponse = await workflowAgent.RunAsync(prompt);
       
        Console.WriteLine("\n\nAfter editing:");
        Console.WriteLine(workflowResponse.Text);
    }
}