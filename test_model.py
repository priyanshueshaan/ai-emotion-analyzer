from transformers import pipeline

model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)

while True:
    text = input("Enter text (or q to quit): ")

    if text.lower() == "q":
        break

    results = model(text)[0]
    top_emotion = max(results, key=lambda x: x["score"])

    print("Emotion:", top_emotion["label"])
    print("Confidence:", round(top_emotion["score"], 4))
    print("-" * 30)
