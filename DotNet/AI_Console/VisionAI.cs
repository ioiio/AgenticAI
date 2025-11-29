using Azure;
using Azure.AI.Inference;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;

namespace AI_Console;

public class VisionAI
{
    public static async Task GetVisionAIResponse()
    {
        var githubToken = Environment.GetEnvironmentVariable("GITHUB_TOKEN");
        if (string.IsNullOrEmpty(githubToken))
        {
            var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();
            githubToken = config["GITHUB_TOKEN"]??"";
        }

        IChatClient chatClient = new ChatCompletionsClient(endpoint: new Uri("https://models.inference.ai.azure.com"), new AzureKeyCredential(githubToken))
                        //.AsIChatClient("gpt-4o-mini");
        .AsIChatClient("Phi-4-multimodal-instruct");// Vision supported model

        // images
        // string imgRunningShoes = "running-shoes.jpg";
        // string imgCarLicense = "license.jpg";
        string imgReceipt = "german-receipt.jpg";

        // prompts
        // var promptDescribe = "Describe the image";
        // var promptAnalyze = "How many red shoes are in the picture? and what other shoes colors are there?";
        // var promptOcr = "What is the text in this picture? Is there a theme for this?";
        var promptReceipt = "I bought the coffee and the sausage. How much do I owe? Add a 18% tip.";

        // prompts
        string systemPrompt = @"You are a useful assistant that describes images using a direct style.";
        var prompt = promptReceipt;//promptOcr;//promptAnalyze;//promptDescribe;
        string imageFileName = imgReceipt;//imgCarLicense;//imgRunningShoes;
        var parentDirectory = Directory.GetParent(Directory.GetCurrentDirectory());
        string image = Path.Combine(parentDirectory?.FullName ?? Directory.GetCurrentDirectory(), "AI_Console/images", imageFileName);

        List<ChatMessage> messages =
        [
            new ChatMessage(Microsoft.Extensions.AI.ChatRole.System, systemPrompt),
            new ChatMessage(Microsoft.Extensions.AI.ChatRole.User, prompt),
        ];

        // read the image bytes, create a new image content part and add it to the messages
        AIContent aic = new DataContent(File.ReadAllBytes(image), "image/jpeg");
        var message = new ChatMessage(Microsoft.Extensions.AI.ChatRole.User, [aic]);
        messages.Add(message);

        // send the messages to the assistant
        var response = await chatClient.GetResponseAsync(messages);
        Console.WriteLine($"Prompt: {prompt}");
        Console.WriteLine($"Image: {imageFileName}");
        Console.WriteLine($"Response: {response.Text}");
    }
}