#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0050
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
namespace AI_Console;
public class RAG_SemKernel 
{
	public static async Task GetRAGResponse() 
    { 
        // system message        
        var systemMessage = "You are a helpful assistant. You reply in short and precise answers, and you explain your responses. If you don't know an answer, you reply 'I don't know'";
		// questions        
        var question = "What is Bruno's favourite super hero?";
		// intro        
        Console.WriteLine($"Question: {question}");
		var modelId = "Phi-4-mini-instruct";
		// Create a chat completion service        
        var builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(modelId: modelId,
        endpoint: new Uri("https://models.inference.ai.azure.com"),
        apiKey: Environment.GetEnvironmentVariable("GITHUB_TOKEN") ?? "");
        builder.AddLocalTextEmbeddingGeneration();
        Kernel kernel = builder.Build();
        var chat = kernel.GetRequiredService<IChatCompletionService>();

		// no memory        
        Console.WriteLine($"{modelId} response (no memory).");
        var history = new ChatHistory();
        history.AddSystemMessage(systemMessage);
		history.AddUserMessage(question);
		var response = chat.GetStreamingChatMessageContentsAsync(history);
		await foreach(var result in response) 
        {   
            //Console.Write(result.ToString());            
            Console.Write(result.Content);
        }

		// separator        
        Console.WriteLine("");
        Console.WriteLine("Press Enter to continue");
        Console.ReadLine();
        Console.WriteLine($"{modelId} response (using semantic memory).");
			
        // Using memory        
        history = new ChatHistory();
        history.AddSystemMessage(systemMessage);
			
        // get the embeddings generator service        
        var embeddingGenerator = kernel.Services.GetRequiredService<ITextEmbeddingGenerationService>();
        var memory = new SemanticTextMemory(new VolatileMemoryStore(), embeddingGenerator);
			
        // add facts to the collection        
        Dictionary<string, string> memoryInformation = new(){
            {"1", "Gisela's favourite super hero is Batman" },
            {"2", "The last super hero movie watched by Gisela was Guardians of the Galaxy Vol 3" },
            {"3", "Bruno's favourite super hero is Invincible" },
            {"4", "The last super hero movie watched by Bruno was Deadpool and Wolverine" },
            {"5", "Bruno does not like the super hero movie: Eternals" }
        };

        const string MemoryCollectionName = "fanFacts";
        foreach(var information in memoryInformation) {
            await memory.SaveInformationAsync(MemoryCollectionName, id: information.Key, text: information.Value);
        }
		
        var memoryResults = memory.SearchAsync(MemoryCollectionName, question, limit: 3, minRelevanceScore: 0.5);
        var memoryContext = "";
        await foreach (var memoryResult in memoryResults){
            memoryContext += $"- {memoryResult.Metadata.Text}\n";
        }
			
		var prompt = $@"Question: {question} Relevant information from memory: {memoryContext} Answer the question using the memory above.";
		history.AddUserMessage(prompt);
		var newResponse = chat.GetStreamingChatMessageContentsAsync(history);
        await foreach(var result in newResponse) {
            Console.Write(result.Content);
        }
        
        Console.WriteLine($"");
    }
}