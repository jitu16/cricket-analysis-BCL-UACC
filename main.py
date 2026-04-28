import os
import json
from analyzer import CareerAnalyzer

def save_analysis_results(data, output_path):
    """
    Saves the processed seasonal statistics to a JSON file in the resource folder.

    Input:
        data (dict): The processed seasonal statistics.
        output_path (str): The destination file path.
    Output:
        None
    """
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Detailed analysis saved to: {output_path}")

def print_seasonal_report(seasonal_stats):
    """
    Formats and prints a detailed bowling report grouped by season.

    Input:
        seasonal_stats (dict): Dictionary keyed by season name with performance lists.
    Output:
        None
    """
    if not seasonal_stats:
        print("No data found for the specified player.")
        return

    for season, matches in seasonal_stats.items():
        total_wickets = sum(m["wickets"] for m in matches)

        print(f"\n{'='*60}")
        print(f" SEASON: {season}")
        print(f" Matches Played: {len(matches)} | Total Wickets: {total_wickets}")
        print(f"{'='*60}")

        for match in matches:
            summary = (
                f"Date: {match['date']} | "
                f"Overs: {match['overs']:>4} | "
                f"Runs: {match['runs']:>3} | "
                f"Wickets: {match['wickets']:>2}"
            )
            print(summary)

            for victim in match["victims"]:
                order = "Top Order" if victim["pos"] <= 3 else "Middle/Tail"
                print(f"  └─ Wicket: {victim['name']} ({victim['runs']} runs, {victim['balls']} balls, SR: {victim['strike_rate']})")
        print(f"{'-'*60}")

def main():
    """
    Orchestrates the analysis by reading from scorecards/ and writing to res/.
    """
    scorecard_directory = "scorecards"
    target_player = "Sajjad"

    filename = f"{target_player}_analysis.json"
    output_file = os.path.join("res", filename)

    if not os.path.exists(scorecard_directory):
        print(f"Error: Input directory '{scorecard_directory}' not found.")
        return

    analyzer = CareerAnalyzer(scorecard_directory)
    stats = analyzer.get_player_stats(target_player)

    print(f"Generating Career Report for: {target_player}")
    print_seasonal_report(stats)

    if stats:
        save_analysis_results(stats, output_file)

if __name__ == "__main__":
    main()
