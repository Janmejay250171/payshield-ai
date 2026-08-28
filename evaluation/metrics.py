import os
import sys

# Ensure the root project directory is in the Python search path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from simulator.engine import PaymentSimulator
from red_team.llm_prompts import AdaptiveMutator

def run_all_experiments():
    print("=" * 65)
    print("PAYSHIELD AI - OFFICIAL HACKATHON EVALUATION SUITE")
    print("=" * 65)

    sim = PaymentSimulator()
    mutator = AdaptiveMutator()

    # -------------------------------------------------------------
    # Experiment 1: Known Attacks (Target: High Recall >95%)[cite: 1]
    # -------------------------------------------------------------
    print("\n[EXPERIMENT 1] Testing Known Attack Families (ATO, Smurfing, Synthetic ID)...")
    exp1_results = sim.run_simulation_batch(count=50, attack_ratio=0.5)
    exp1_attacks = [r for r in exp1_results if r["transaction"]["attack_family"] != "NONE"]
    exp1_blocked = [r for r in exp1_attacks if r["result"]["decision"] == "BLOCK"]
    
    recall = (len(exp1_blocked) / len(exp1_attacks)) * 100 if exp1_attacks else 0.0
    print(f"-> Total Attacks Generated : {len(exp1_attacks)}")
    print(f"-> Total Attacks Blocked   : {len(exp1_blocked)}")
    print(f"-> Known Attack Catch Rate : {recall:.2f}%")

    # -------------------------------------------------------------
    # Experiment 2: Zero-Day Behavioral Anomaly (Isolation Forest)[cite: 1]
    # -------------------------------------------------------------
    print("\n[EXPERIMENT 2] Testing Zero-Day Vector (AI Impersonation)...")
    zero_day_txns = sim.red_team.generate_attack(family="AI_IMPERSONATION")
    zero_day_caught = 0
    for z in zero_day_txns:
        res = sim.risk_engine.score_transaction(z)
        if res["decision"] in ["BLOCK", "REVIEW"]:
            zero_day_caught += 1
    print(f"-> Zero-Day Detection Rate : {(zero_day_caught / len(zero_day_txns))*100:.2f}%")

    # -------------------------------------------------------------
    # Experiment 3 & 4: Adaptive Mutation & Defense Resilience Loop[cite: 1]
    # -------------------------------------------------------------
    print("\n[EXPERIMENT 3 & 4] Adversarial Adaptation Loop (Red Mutates vs Blue Responds)...")
    initial_attack = sim.red_team.generate_attack(family="ACCOUNT_TAKEOVER")[0]
    first_res = sim.risk_engine.score_transaction(initial_attack)
    print(f"-> Gen 0 Attack Result: {first_res['decision']} (Score: {first_res['risk_score']})")

    mutated_attack = mutator.mutate_payload(initial_attack, first_res["reasons"])
    mutated_res = sim.risk_engine.score_transaction(mutated_attack)
    print(f"-> Gen 1 (Mutated Attack) Result: {mutated_res['decision']} (Score: {mutated_res['risk_score']})")
    print(f"   Sub-scores  : {mutated_res['sub_scores']}")
    print(f"   Explanation : {mutated_res['reasons']}")

    print("\n" + "=" * 65)
    print(f"OVERALL DEFENSE RESILIENCE SCORE: {sim.metrics['resilience_score']:.2f}%")
    print("=" * 65)

if __name__ == "__main__":
    run_all_experiments()