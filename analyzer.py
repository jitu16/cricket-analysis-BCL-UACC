import json
import os
from datetime import datetime

class CareerAnalyzer:
    """
    Analyzes cricket scorecard JSONs to extract season-specific bowling stats
    and detailed victim performance metrics.
    """

    def __init__(self, scorecard_dir):
        """
        Initializes the analyzer with the target directory.

        Input: scorecard_dir (str)
        Output: None
        """
        self.scorecard_dir = scorecard_dir

    def _convert_balls_to_overs(self, balls):
        """
        Converts total balls into standard cricket over notation.

        Input: balls (int)
        Output: float
        """
        return (balls // 6) + (balls % 6) / 10

    def _extract_victims(self, batters, bowler_id):
        """
        Scans a batting list to identify victims where the player was the BOWLER.
        """
        victims = []
        target_id = str(bowler_id).strip()

        for pos, batter in enumerate(batters, start=1):
            # wicketTaker1 is universally the bowler in CricClubs.
            wt1 = str(batter.get("wicketTaker1", "")).strip()

            # Only credit if they are the primary wicket taker and it's not a run out
            if wt1 == target_id and batter.get("howOut") != "ro" and batter.get("howOut") != "mk":
                runs = batter.get("runsScored", 0)
                balls = batter.get("ballsFaced", 0)
                sr = (runs / balls * 100) if balls > 0 else 0.0

                victims.append({
                    "name": batter.get("playerName", "").strip(),
                    "playerID": batter.get("playerID", "").strip(),
                    "runs": runs,
                    "balls": balls,
                    "strike_rate": round(sr, 2),
                    "pos": pos
                })
        return victims

    def _process_innings_pair(self, data, target_name, filename):
        """
        Processes each innings individually to match bowlers with their victims.

        Input:
            data (dict): The match data dictionary.
            target_name (str): The name of the player to analyze.
            filename (str): The name of the file being processed for error reporting.
        Output:
            list: A list of match performance dictionaries.
        """
        performances = []
        for i_key in ["innings1", "innings2"]:
            innings = data.get(i_key)
            if not innings:
                continue

            bowler = next((b for b in innings.get("bowling", [])
                          if target_name.lower() in b.get("firstName", "").lower() or
                             target_name.lower() in b.get("lastName", "").lower()), None)

            if bowler:
                batters = innings.get("batting", [])
                bowler_id = bowler.get("playerID")
                claimed_wickets = bowler.get("wickets", 0)

                victims = self._extract_victims(batters, bowler_id)

                assert len(victims) == claimed_wickets, (
                    f"DATA CORRUPTION DETECTED in {filename}: {target_name} summary claims {claimed_wickets} wickets, "
                    f"but successfully mapped {len(victims)} victims in the batting list."
                )

                performances.append({
                    "overs": self._convert_balls_to_overs(bowler.get("balls", 0)),
                    "runs": bowler.get("runs", 0),
                    "wickets": claimed_wickets,
                    "victims": victims
                })

        return performances

    def get_player_stats(self, target_player_name):
        all_performances = []
        files = [f for f in os.listdir(self.scorecard_dir) if f.endswith('.json')]

        for filename in files:
            filepath = os.path.join(self.scorecard_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_json = json.load(f)

            match_data = raw_json.get("data", {})
            match_info = match_data.get("matchInfo", {})
            season = match_info.get("seriesName") or match_data.get("seriesName") or "Unknown Season"

            match_perfs = self._process_innings_pair(match_data, target_player_name, filename)

            for perf in match_perfs:
                perf["season"] = season
                perf["date"] = filename.split('_')[1]
                all_performances.append(perf)

        all_performances.sort(key=lambda x: datetime.strptime(x['date'], '%m-%d-%Y'))

        seasonal_data = {}
        for perf in all_performances:
            s = perf.pop("season")
            if s not in seasonal_data:
                seasonal_data[s] = []
            seasonal_data[s].append(perf)

        return seasonal_data
