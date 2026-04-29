import json
import os
from scipy.stats import ttest_ind

def load_player_data(player_name):
    """
    Loads the processed seasonal statistics for a specific player.
    """
    filepath = os.path.join("res", f"{player_name}_analysis.json")
    if not os.path.exists(filepath):
        print(f"Error: Data file for {player_name} not found at {filepath}")
        return {}
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)

def filter_matches(player_data, target_seasons):
    """
    Extracts matches specifically from the requested seasons.
    If target_seasons is "ALL", it aggregates the entire career.
    """
    matches = []
    for season, season_matches in player_data.items():
        if target_seasons == "ALL" or season in target_seasons:
            matches.extend(season_matches)
    return matches

def extract_metric_arrays(matches):
    """
    Extracts numerical arrays for match-level and victim-level metrics.
    """
    metrics = {
        "economy": [],
        "match_sr": [],
        "match_ave": [],
        "victim_pos": [],
        "victim_runs": [],
        "victim_sr": [],
        "wickets_per_match": [],
        "overs_per_match": []
    }

    for match in matches:
        overs = match.get("overs", 0)
        runs = match.get("runs", 0)
        wickets = match.get("wickets", 0)

        metrics["overs_per_match"].append(overs)
        metrics["wickets_per_match"].append(wickets)

        if overs > 0:
            metrics["economy"].append(runs / overs)

        if wickets > 0:
            metrics["match_ave"].append(runs / wickets)
            metrics["match_sr"].append((overs * 6) / wickets)

        for victim in match.get("victims", []):
            metrics["victim_pos"].append(victim.get("pos", 0))
            metrics["victim_runs"].append(victim.get("runs", 0))
            metrics["victim_sr"].append(victim.get("strike_rate", 0.0))

    return metrics

def calculate_statistical_significance(metrics_a, metrics_b):
    """
    Performs a Welch's t-test across all metric arrays.
    """
    results = {}
    for key in metrics_a.keys():
        arr1 = metrics_a[key]
        arr2 = metrics_b[key]

        # We need at least 2 data points in both arrays to run a t-test
        if len(arr1) > 1 and len(arr2) > 1:
            t_stat, p_val = ttest_ind(arr1, arr2, equal_var=False)
            results[key] = {
                "t_stat": t_stat,
                "p_value": p_val,
                "mean_a": sum(arr1) / len(arr1),
                "mean_b": sum(arr2) / len(arr2)
            }
        else:
            results[key] = None # Not enough data

    return results

def generate_markdown_report(config_a, config_b, results, count_a, count_b):
    """
    Generates a professional Markdown report and saves it to the res folder.
    """
    # Construct a safe filename
    filename = f"{config_a['player']}-{config_a['label']}-vs-{config_b['player']}-{config_b['label']}.md"
    filename = filename.replace(" ", "_").replace("/", "-")
    filepath = os.path.join("markdown", filename)

    md = [
        f"# Head-to-Head Analysis: {config_a['label']} vs {config_b['label']}\n",
        "## Configuration Profiles",
        f"**Player A Name: {config_a['player']}**",
        f"- Label: {config_a['label']}",
        f"- Seasons Included: {', '.join(config_a['seasons']) if isinstance(config_a['seasons'], list) else config_a['seasons']}",
        f"- Matches Analyzed: {count_a}\n",
        f"**Player B Name: {config_b['player']}**",
        f"- Label: {config_b['label']}",
        f"- Seasons Included: {', '.join(config_b['seasons']) if isinstance(config_b['seasons'], list) else config_b['seasons']}",
        f"- Matches Analyzed: {count_b}\n",
        "## Statistical Significance Table (Welch's t-test)",
        "| Metric | Mean (A) | Mean (B) | P-Value | Significant? (< 0.05) |",
        "|---|---|---|---|---|"
    ]

    for metric, res in results.items():
        metric_name = metric.replace('_', ' ').title()
        if res is None:
            md.append(f"| {metric_name} | N/A | N/A | N/A | Insufficient Data |")
        else:
            sig_marker = "**YES**" if res['p_value'] < 0.05 else "NO"
            row = f"| {metric_name} | {res['mean_a']:.2f} | {res['mean_b']:.2f} | {res['p_value']:.4f} | {sig_marker} |"
            md.append(row)

    md.append("\n## Conclusion summary")
    md.append("*Note: A p-value of less than 0.05 indicates a statistically significant difference between the two datasets, suggesting the variance is not due to random chance.*")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"\n[SUCCESS] Markdown report generated: {filepath}")


def main():
    """
    Orchestrates the dynamic comparison. Configure Entity A and B below.
    """
    # --- CONFIGURATION ZONE ---

    # Example 1: Comparing your Pace vs Spin
    # config_a = {
    #     "player": "Jitu",
    #     "label": "Pace",
    #     "seasons": ["BCL T20 2021", "BCL T25 2022", "BCL T20 2022", "BCL T25 2023", "BCL T25 2024"]
    # }

    # config_b = {
    #     "player": "Jitu",
    #     "label": "Spin",
    #     "seasons": ["BCL T20 2024", "BCL T25 2025", "BCL T20 2025", "BCL T25 2026"]
    # }

    # Example 2: Comparing your entire career vs someone else's
    config_a = {
        "player": "Sajjad",
        "label": "Full_Career",
        "seasons": "ALL"
    }

    config_b = {
        "player": "Halim",
        "label": "Full_Career",
        "seasons": "ALL"
    }


    data_a = load_player_data(config_a["player"])
    data_b = load_player_data(config_b["player"])

    if not data_a or not data_b:
        return

    matches_a = filter_matches(data_a, config_a["seasons"])
    matches_b = filter_matches(data_b, config_b["seasons"])

    metrics_a = extract_metric_arrays(matches_a)
    metrics_b = extract_metric_arrays(matches_b)

    results = calculate_statistical_significance(metrics_a, metrics_b)

    generate_markdown_report(config_a, config_b, results, len(matches_a), len(matches_b))


if __name__ == "__main__":
    main()
