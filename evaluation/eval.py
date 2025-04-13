import os
import json
import csv
import sys
from typing import List, Dict

# project path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

# environment variables
from dotenv import load_dotenv
ec2_env_path = "/home/ec2-user/websocket-handler/.env"
local_env_path = os.path.join(project_root, ".env")
if os.path.exists(ec2_env_path):
    load_dotenv(dotenv_path=ec2_env_path)
else:
    load_dotenv(dotenv_path=local_env_path)

from agents.curriculum_agent import CurriculumAgent
import evaluate

# load metrics
rouge = evaluate.load("rouge")
bertscore = evaluate.load("bertscore")
bleu = evaluate.load("bleu")

test_data = [
    {
        "query": "What are the career outcomes for Duke AI MEng students?",
        "ground_truth": "Graduates of the Duke AI MEng program go on to work in top tech companies and research institutions, often in roles related to artificial intelligence, data science, and machine learning."
    },
    {
        "query": "What is the class size for the Duke AI program?",
        "ground_truth": "The class size for the Duke AI MEng program is kept intentionally small to foster close collaboration, with approximately 30-40 students per cohort."
    },
    {
        "query": "How much does the AI MEng program at Duke cost?",
        "ground_truth": "Tuition for the AI MEng program at Duke is approximately $60,000, excluding additional fees and living expenses."
    },
    {
        "query": "What is the curriculum structure for the Duke AI MEng program?",
        "ground_truth": "The Duke AI MEng program includes core courses in AI fundamentals, electives in machine learning and deep learning, and a capstone project."
    },
    {
        "query": "Can the AI MEng program at Duke be completed online?",
        "ground_truth": "The AI MEng program at Duke is designed for on-campus, in-person learning but there is an online option."
    },
    {
        "query": "Is the Duke AI MEng program STEM-designated?",
        "ground_truth": "Yes, the Duke AI MEng program is officially STEM-designated, which benefits international students seeking OPT extensions."
    },
    {
        "query": "When is the application deadline for Duke’s AI MEng program?",
        "ground_truth": "The priority application deadline for the Duke AI MEng program is typically in January, with rolling admissions afterward."
    },
    {
        "query": "How can international students apply to Duke’s AI MEng?",
        "ground_truth": "International students must submit TOEFL/IELTS scores, transcripts, a resume, and a statement of purpose as part of the Duke AI MEng application."
    },
    {
        "query": "What financial aid is available for Duke AI MEng students?",
        "ground_truth": "Financial aid for Duke AI MEng students includes limited merit-based scholarships and opportunities for teaching assistantships."
    },
    {
        "query": "How long does it take to complete the AI MEng program at Duke?",
        "ground_truth": "The Duke AI MEng program has a 12 month and 16 month option. Additionally, the online option takes 3 to 4 semesters to complete, depending on course load."
    },
    {
        "query": "What are the core strengths of Duke’s Pratt School of Engineering?",
        "ground_truth": "Duke’s Pratt School of Engineering is known for its interdisciplinary research, small class sizes, and strong industry partnerships."
    },
    {
        "query": "How diverse is the student body at Duke Engineering?",
        "ground_truth": "Duke Engineering emphasizes diversity and inclusion, with initiatives to support underrepresented students and foster community."
    },
    {
        "query": "What makes Duke’s AI MEng program unique?",
        "ground_truth": "Duke’s AI MEng program offers a blend of technical rigor and professional development."
    },
    {
        "query": "Where is Duke University located?",
        "ground_truth": "Duke University is located in Durham, North Carolina."
    },
    {
        "query": "What kind of events does Duke host for admitted engineering students?",
        "ground_truth": "Duke hosts events like admitted student days, webinars, and networking sessions to help admitted students explore campus life and connect with students and faculty."
    },
    {
        "query": "How can I attend a Duke Pratt info session?",
        "ground_truth": "You can register for a Duke Pratt info session online through the admissions events calendar."
    },
    {
        "query": "What is life like in Durham for Duke graduate students?",
        "ground_truth": "Durham offers a vibrant food scene, outdoor activities, and affordable living, making it a great place for Duke grad students."
    },
    {
        "query": "Are there student clubs and organizations for Duke AI students?",
        "ground_truth": "Yes, Duke AI MEng students can join clubs like the Duke AI Society and participate in hackathons and tech meetups."
    },
    {
        "query": "What housing options are available for Duke grad students?",
        "ground_truth": "Duke offers graduate student housing near campus and provides resources for finding off-campus apartments in Durham."
    },
    {
        "query": "How do I contact admissions for the Duke AI MEng program?",
        "ground_truth": "You can contact Duke AI MEng admissions via email or phone, as listed on the official program website."
    }
]

def evaluate_responses(agent: CurriculumAgent, data: List[Dict[str, str]]) -> List[Dict]:
    results = []
    for item in data:
        query = item["query"]
        reference = item["ground_truth"]

        # chatbot response
        response = agent.agent.run(query)

        # compute metrics
        rouge_scores = rouge.compute(predictions=[response], references=[reference])
        bert_scores = bertscore.compute(predictions=[response], references=[reference], lang="en")
        bleu_score = bleu.compute(predictions=[response], references=[reference])

        results.append({
            "query": query,
            "response": response,
            "ground_truth": reference,
            "rougeL": rouge_scores["rougeL"],
            "bertscore_f1": bert_scores["f1"][0],
            "bleu": bleu_score["bleu"]
        })

    return results

def save_results_to_csv(results: List[Dict], filename: str = "llm_eval_results.csv"):
    if not results:
        print("No results to save.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def main():
    agent = CurriculumAgent()
    results = evaluate_responses(agent, test_data)
    save_results_to_csv(results)
    print("Evaluation complete. Results saved to llm_eval_results.csv.")

if __name__ == "__main__":
    main()
