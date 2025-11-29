using Azure.AI.Inference;
using Azure;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.Extensions.AI;
using System.Text;

namespace AI_Console;

public class RAG_SemKernel2
{
    public static async Task GetRAGResponse()
    {
        var chatModelId = "Phi-4-mini-instruct";
        var embeddingModelId = "text-embedding-3-small"; // Use an embedding model
        var vectorStore = new InMemoryVectorStore();

        // get movie list
        var movies = vectorStore.GetCollection<int, MovieVector<int>>("movies");
        await movies.EnsureCollectionExistsAsync();
        var movieData = MovieFactory<int>.GetMovieVectorList();

        // get embeddings generator and generate embeddings for movies
        var client = new EmbeddingsClient(new Uri("https://models.inference.ai.azure.com"), 
            new AzureKeyCredential(Environment.GetEnvironmentVariable("GITHUB_TOKEN") ?? ""));

        IEmbeddingGenerator<string, Embedding<float>> generator = client.AsIEmbeddingGenerator(embeddingModelId);

        foreach (var movie in movieData){
            movie.Vector = await generator.GenerateVectorAsync(movie.Description);
            await movies.UpsertAsync(movie);
        }

        // perform the search
        var query = "A family friendly movie that includes virtual reality created by machines";
        var queryEmbedding = await generator.GenerateVectorAsync(query);

        // Retrieve relevant movies
        var retrievedMovies = new List<MovieVector<int>>();
        await foreach (var resultItem in movies.SearchAsync(queryEmbedding, top: 1)){
            Console.WriteLine($"Retrieved - Title: {resultItem.Record.Title}");
            Console.WriteLine($"Description: {resultItem.Record.Description}");
            Console.WriteLine($"Score: {resultItem.Score}");
            Console.WriteLine();
            retrievedMovies.Add(resultItem.Record);
        }

        // Generate response using the retrieved context
        var chatClient = new ChatCompletionsClient(
            new Uri("https://models.inference.ai.azure.com"),
            new AzureKeyCredential(Environment.GetEnvironmentVariable("GITHUB_TOKEN") ?? ""));

        IChatClient chatGenerator = chatClient.AsIChatClient(chatModelId);

        // Build context from retrieved movies
        var contextBuilder = new StringBuilder();
        contextBuilder.AppendLine("Here are some relevant movies from our database:");
        contextBuilder.AppendLine();

        foreach (var movie in retrievedMovies){
        contextBuilder.AppendLine($"Title: {movie.Title}");
        contextBuilder.AppendLine($"Description: {movie.Description}");
        contextBuilder.AppendLine();
        }

        // Create the prompt with context
        var prompt = $@"Based on the following movie information: {contextBuilder}
        User Question: {query}
        Please provide a detailed recommendation explaining which movie(s) best match the user's request and why.";

        Console.WriteLine("=== RAG Generated Response ===");
        Console.WriteLine();

        // Generate the response
        var response = await chatGenerator.GetResponseAsync(prompt);
        Console.WriteLine(response.Text);
    }
}