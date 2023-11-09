from services.openAIService import OpenAIService
from services.pineconeService import PineconeService
import json

def main():
    print("Please paste your multi-line string here. Enter 'END' on a new line when finished:")

    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)

    text = '\n'.join(lines)

    openai_service = OpenAIService()
    embeddings_data = openai_service.generate_embeddings(text)
    embeddings = embeddings_data['data'][0]['embedding']

    pinecone_service = PineconeService()
    results = pinecone_service.query(embeddings, 5)

    # Extract only id and score from each match
    simplified_results = [{'id': match['id'], 'score': match['score']} for match in results['matches']]
    print(simplified_results)
    with open('results.json', 'w') as f:
        json.dump(simplified_results, f)

if __name__ == "__main__":
    main()