import os
import sys
import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Add current directory to path for imports
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cosine_sim(v1, v2):
    """Computes cosine similarity between two vectors using numpy."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2) if norm_v1 > 0 and norm_v2 > 0 else 0.0

def calculate_diversity():
    log_file = "logs/metrics_data.jsonl"
    report_file = "reports/creativity_report.md"
    
    if not os.path.exists(log_file):
        logger.error(f"Log file {log_file} not found.")
        return

    scripts = []
    # We want the last 15 valid scripts
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    output_text = data.get("output_text", "").strip()
                    # Filter out empty or very short outputs (like errors or empty responses)
                    if output_text and len(output_text) > 50:
                        scripts.append(output_text)
                    if len(scripts) >= 15:
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return

    if len(scripts) < 2:
        logger.warning(f"Not enough valid scripts found in logs (found {len(scripts)}). Diversity calculation needs at least 2.")
        return

    logger.info(f"Analyzing {len(scripts)} scripts for creative diversity...")
    
    # Initialize the model (same as SemanticCacheService)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(scripts)
    
    num_scripts = len(scripts)
    sim_scores = []
    pairs = []

    # Calculate all pairwise similarities
    for i in range(num_scripts):
        for j in range(i + 1, num_scripts):
            sim = cosine_sim(embeddings[i], embeddings[j])
            sim_scores.append(sim)
            pairs.append((sim, i, j))
    
    avg_sim = np.mean(sim_scores)
    diversity_score = 1 - avg_sim
    
    # Sort pairs by similarity to find the most redundant ones
    pairs.sort(key=lambda x: x[0], reverse=True)
    top_3 = pairs[:3]
    
    # Recommendations based on user requirement
    if avg_sim > 0.8:
        recommendation = "Vaš model je trenutno u 'Repetitive' zoni (Similarity > 0.8), preporučuje se povećanje temperature u promptu."
    elif avg_sim > 0.6:
        recommendation = "Diverzitet je umeren. Razmislite o variranju 'system' prompta za veću kreativnost."
    else:
        recommendation = "Odličan diverzitet! Model generiše veoma različite skripte."

    # Markdown Report Generation
    report_content = f"""# 🎨 Creative Diversity Report

## 📊 Diversity Metrics
- **Diversity Score**: `{diversity_score:.4f}` (Scale 0.0 - 1.0, where 1.0 is maximum diversity)
- **Average Pairwise Similarity**: `{avg_sim:.4f}`
- **Sample Size**: `{num_scripts}` skripti (poslednjih 15 iz logova).

## 🧐 Recommendation
> {recommendation}

## 🔥 Top 3 Most Similar Pairs (Redundancy Check)
"""
    for score, i, j in top_3:
        # Extract a snippet of the script (it's often JSON, so we try to make it readable)
        script_a = scripts[i]
        script_b = scripts[j]
        
        # Try to parse and get the hook if it's JSON
        try:
            a_json = json.loads(script_a)
            a_preview = a_json.get("hook", script_a[:100])
        except:
            a_preview = script_a[:100]
            
        try:
            b_json = json.loads(script_b)
            b_preview = b_json.get("hook", script_b[:100])
        except:
            b_preview = script_b[:100]

        report_content += f"""
### Similarity: `{score:.4f}`
- **Script A**: `{a_preview}...`
- **Script B**: `{b_preview}...`
---
"""

    # Save the report
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"✅ Diversity calculation complete.")
    print(f"📊 Diversity Score: {diversity_score:.4f}")
    print(f"📄 Report saved to: {report_file}")

if __name__ == "__main__":
    calculate_diversity()
