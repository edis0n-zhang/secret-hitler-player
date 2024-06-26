# What We Did
We made LLMs play the popular deception game Secret Hitler.

# How We Did It
1. Passed in relevant information to each player: Their known information (board state, fascists if they are a fascist, etc.)
2. Chunked and uploaded strategy docs to a vector database and pull relevant strategy using RAG
3. The rules of the stage and their goal
4. Gave a history of the discussions between players (discussed before voting and after enacting a policy)

# How to Run
Place your openai key in a .env file in the simulator folder: `OPENAI_API_KEY="INSERT YOUR KEY HERE"`

Clone the repository, `cd` into simulator, and run `python HitlerGame.py`.

# Tech Stack
1. Pinecone Vector DB
2. OpenAI Embeddings + GPT-4o

![Tech Stack](techstack.png)

# Credits
Secret Hitler Simulator We Built On: https://github.com/Mycleung/Secret-Hitler

Strategy Docs: https://secrethitler.tartanllama.xyz/
