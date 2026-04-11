import json
import os
import sys
import time
import argparse
import random

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.align import Align

# Ensure src is in path
sys.path.append(os.getcwd())
from src.core.config import settings

console = Console()

# Set OpenAI key for DeepEval
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY.get_secret_value()

LOG_FILE = "logs/metrics_data.jsonl"
REPORT_FILE = "reports/advanced_metrics.md"
EVAL_MODEL = "gpt-4o-mini"

# Define a much stricter rubric for the judge
VIRAL_METRIC = GEval(
    name="Viral Script Integrity",
    criteria="""
    1. Hook Strength: Is the first sentence impossible to scroll past? (Must be < 5 words)
    2. Pacing: Does every sentence move the story forward? (No fluff)
    3. Structural Integrity: Does it follow the 3-act viral structure (Hook, Value, CTA)?
    4. Tone Consistency: Is it energetic and punchy throughout?
    5. Call to Action: Is there a clear, high-friction CTA at the end?
    """,
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model=EVAL_MODEL
)

class AnalyticsResult(BaseModel):
    request_id: str
    model_name: str
    prompt_version: str
    self_score: float
    external_score: float
    calibration_gap: float
    cost_usd: float
    roi: float

def run_analytics(num_examples: int = 5, use_random: bool = False, version: str = None):
    console.clear()
    console.print("\n")
    
    header_text = "[bold cyan]VIRAL ENGINE[/bold cyan] • [white]Advanced Engineering Analytics[/white]"
    if version:
        header_text += f" • [yellow]Filter: v{version}[/yellow]"
    if use_random:
        header_text += " • [magenta]Random Sampling[/magenta]"
    else:
        header_text += " • [magenta]Latest Entries[/magenta]"
        
    header = Panel.fit(
        header_text,
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(header)
    
    if not os.path.exists(LOG_FILE):
        console.print(f"[red]❌ Log file {LOG_FILE} not found.[/red]")
        return

    with open(LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    
    entries = [json.loads(line) for line in lines]
    
    # Filter by version if specified
    if version:
        entries = [e for e in entries if e.get("prompt_version") == version]
        if not entries:
            console.print(f"[red]❌ No entries found for version {version}.[/red]")
            return

    # Select entries
    if use_random:
        selected_entries = random.sample(entries, min(len(entries), num_examples))
    else:
        selected_entries = entries[-num_examples:]
    
    results = []

    # Create table with fit-to-content width
    table = Table(
        title="[bold white]Model Calibration & Quality Audit[/bold white]",
        caption=f"[dim]DeepEval GEval • Metric: Viral Integrity v1.2 • N={len(selected_entries)}[/dim]",
        show_header=True, 
        header_style="bold magenta",
        box=box.ROUNDED,
        expand=False,
        title_justify="left"
    )
    table.add_column("Trace ID", style="dim", width=12)
    table.add_column("V", style="yellow", width=6)
    table.add_column("Model", style="cyan")
    table.add_column("Self-Audit", justify="right")
    table.add_column("Judge", justify="right")
    table.add_column("Gap (MCE)", justify="right")
    table.add_column("ROI", justify="right")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        console=console,
        transient=True
    ) as progress:
        eval_task = progress.add_task("[yellow]Analyzing performance...", total=len(selected_entries))
        
        with Live(table, refresh_per_second=4):
            for entry in selected_entries:
                request_id = entry.get("request_id", "N/A")[:8]
                prompt_version = entry.get("prompt_version", "?.?.?")
                input_text = entry.get("input_text", "")
                output_text = entry.get("output_text", "")
                self_score = entry.get("self_audit_hook_strength", 0.0)
                cost_usd = entry.get("cost_usd", 0.0)
                
                if not input_text or not output_text:
                    progress.advance(eval_task)
                    continue

                try:
                    test_case = LLMTestCase(
                        input=input_text,
                        actual_output=output_text
                    )
                    
                    VIRAL_METRIC.measure(test_case)
                    external_score = VIRAL_METRIC.score if VIRAL_METRIC.score is not None else 0.0
                    
                    calibration_gap = abs(self_score - external_score)
                    roi = (external_score * 10) / (cost_usd * 1000) if cost_usd > 0 else 0.0 
                    
                    res = AnalyticsResult(
                        request_id=request_id,
                        model_name=entry.get("model_name", "unknown"),
                        prompt_version=prompt_version,
                        self_score=self_score,
                        external_score=external_score,
                        calibration_gap=round(calibration_gap, 4),
                        cost_usd=cost_usd,
                        roi=round(roi, 2)
                    )
                    results.append(res)
                    
                    gap_color = "green" if calibration_gap < 0.10 else "yellow" if calibration_gap < 0.20 else "red"
                    roi_style = "bold green" if roi > 50 else "white"
                    
                    table.add_row(
                        request_id,
                        prompt_version,
                        res.model_name,
                        f"{self_score:.2f}",
                        f"{external_score:.2f}",
                        f"[{gap_color}]{calibration_gap:.4f}[/{gap_color}]",
                        f"[{roi_style}]{roi:,.1f}x[/{roi_style}]"
                    )
                    
                except Exception:
                    pass
                
                progress.advance(eval_task)

    # Final Summary (Multi-line and Versioned)
    if results:
        from collections import defaultdict
        version_groups = defaultdict(list)
        roi_groups = defaultdict(list)
        for r in results:
            version_groups[r.prompt_version].append(r.calibration_gap)
            roi_groups[r.prompt_version].append(r.roi)
        
        summary_lines = []
        summary_lines.append("[bold cyan]Efficiency & Quality Audit[/bold cyan]")
        summary_lines.append("─" * 45)
        
        # Calculate MCE and ROI for each version
        for v in sorted(version_groups.keys()):
            gaps = version_groups[v]
            rois = roi_groups[v]
            
            v_mce = sum(gaps) / len(gaps)
            v_roi = sum(rois) / len(rois)
            
            mce_color = "green" if v_mce < 0.10 else "yellow" if v_mce < 0.20 else "red"
            roi_color = "bold green" if v_roi > 50 else "white"
            
            summary_lines.append(f"• [bold white]Version {v}:[/bold white]")
            summary_lines.append(f"  └─ MCE: [{mce_color}]{v_mce:.4f}[/{mce_color}] | ROI: [{roi_color}]{v_roi:,.1f}x[/{roi_color}]")
        
        summary_lines.append("─" * 45)
        
        # Glossary / Formulas
        summary_lines.append("[bold dim]Glossary & Formulas:[/bold dim]")
        summary_lines.append("[dim]• MCE: Mean Calibration Error (Avg |Self - Judge|)[/dim]")
        summary_lines.append("[dim]• ROI: Quality-to-Cost (Judge Score / USD Cost)[/dim]")
        
        summary_lines.append("─" * 45)
        summary_lines.append(f"[bold white]Report:[/bold white] [underline]{REPORT_FILE}[/underline]")
        
        summary_panel = Panel.fit(
            "\n".join(summary_lines),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        console.print(summary_panel)
        console.print("\n")
        
        generate_markdown_report(results)

def generate_markdown_report(results: list[AnalyticsResult]):
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🔬 Advanced AI Quality Report\n\n")
        f.write(f"Audit Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 📊 Model Calibration & Efficiency\n\n")
        f.write("| Trace ID | V | Model | Self Score | Judge Score | MCE | ROI |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |\n")
        for r in results:
            f.write(f"| {r.request_id} | {r.prompt_version} | {r.model_name} | {r.self_score:.2f} | {r.external_score:.2f} | {r.calibration_gap:.4f} | {r.roi:.1f}x |\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Viral Engine Advanced Analytics")
    parser.add_argument("--num", type=int, default=5, help="Number of examples to analyze")
    parser.add_argument("--random", action="store_true", help="Sample randomly from the logs")
    parser.add_argument("--version", type=str, default=None, help="Filter by prompt version (e.g. 1.0.0)")
    
    args = parser.parse_args()
    run_analytics(num_examples=args.num, use_random=args.random, version=args.version)
