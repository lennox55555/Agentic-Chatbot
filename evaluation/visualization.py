import pandas as pd
import matplotlib.pyplot as plt

# load evaluation results
df = pd.read_csv("llm_eval_results.csv")

plt.figure(figsize=(14, 6))

bar_width = 0.2
x = range(len(df))

plt.bar([i - 1.5 * bar_width for i in x], df["rougeL"], width=bar_width, label="ROUGE-L")
plt.bar([i - 0.5 * bar_width for i in x], df["bertscore_f1"], width=bar_width, label="BERTScore F1")
plt.bar([i + 0.5 * bar_width for i in x], df["bleu"], width=bar_width, label="BLEU")

# bar chart of scores per question
plt.xlabel("Query Index")
plt.ylabel("Score")
plt.title("LLM Evaluation Metrics per Query")
plt.xticks(x, [f"Q{i+1}" for i in x], rotation=45)
plt.ylim(0, 1.1)
plt.legend()
plt.tight_layout()
plt.grid(True, linestyle="--", alpha=0.5)

plt.show()

# average values for each metric
avg_metrics = {
    "ROUGE-L": df["rougeL"].mean(),
    "BERTScore-F1": df["bertscore_f1"].mean(),
    "BLEU": df["bleu"].mean()
}

# bar chart of the average metrics
plt.figure(figsize=(8, 5))
plt.bar(avg_metrics.keys(), avg_metrics.values())
plt.ylabel("Score")
plt.title("Average Evaluation Metrics")
plt.ylim(0, 1)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()