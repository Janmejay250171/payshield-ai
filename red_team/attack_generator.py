import random
from datetime import datetime


class RedTeamAttackGenerator:

    def __init__(self):

        self.attack_families = [
            "ACCOUNT_TAKEOVER",
            "SYNTHETIC_IDENTITY",
            "AI_IMPERSONATION",
            "SMURFING",
            "ADAPTIVE_MUTATION",
        ]

    def generate_attack(
        self,
        family: str = None,
        mutation_context: dict = None,
    ) -> list[dict]:

        if not family:
            family = random.choice(
                self.attack_families
            )

        txns = []

        now_str = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # =====================================================
        # ACCOUNT TAKEOVER
        # =====================================================

        if family == "ACCOUNT_TAKEOVER":

            user_id = (
                f"USER_{random.randint(1, 100):04d}"
            )

            for _ in range(3):

                txns.append({

                    "transaction_id":
                        f"ATO_{random.randint(100000, 999999)}",

                    "user_id":
                        user_id,

                    "amount":
                        round(
                            random.uniform(
                                75000,
                                120000,
                            ),
                            2,
                        ),

                    "transaction_type":
                        "TRANSFER",

                    "country":
                        "Russia",

                    "device_type":
                        "unknown",

                    "device_id":
                        "ATO_UNKNOWN_DEVICE",

                    "ip_address":
                        "185.220.101.5",

                    "timestamp":
                        now_str,

                    "seconds_since_prev":
                        5.0,

                    "velocity_1h":
                        720,

                    "attack_family":
                        "ACCOUNT_TAKEOVER",
                })

        # =====================================================
        # SYNTHETIC IDENTITY
        # =====================================================

        elif family == "SYNTHETIC_IDENTITY":

            shared_device = (
                f"DEVICE_EMULATOR_"
                f"{random.randint(10, 99)}"
            )

            shared_ip = (
                "192.168.4.101"
            )

            for i in range(6):

                txns.append({

                    "transaction_id":
                        f"SYNTH_{random.randint(100000, 999999)}",

                    "user_id":
                        f"SYNTH_USER_{i:04d}",

                    "amount":
                        round(
                            random.uniform(
                                15000,
                                35000,
                            ),
                            2,
                        ),

                    "transaction_type":
                        "PAYMENT",

                    "country":
                        "India",

                    "device_type":
                        "mobile",

                    "device_id":
                        shared_device,

                    "ip_address":
                        shared_ip,

                    "timestamp":
                        now_str,

                    "seconds_since_prev":
                        60.0,

                    "velocity_1h":
                        60,

                    "attack_family":
                        "SYNTHETIC_IDENTITY",
                })

        # =====================================================
        # SMURFING
        # =====================================================

        elif family == "SMURFING":

            # One common recipient receives funds
            # from multiple independent accounts.

            collector = (
                f"MULE_ACCOUNT_"
                f"{random.randint(1000, 9999)}"
            )

            for i in range(6):

                txns.append({

                    "transaction_id":
                        f"SMURF_{random.randint(100000, 999999)}",

                    "user_id":
                        f"SMURF_SRC_{i:04d}",

                    # CRITICAL:
                    # All transactions go to the same mule.
                    "recipient_id":
                        collector,

                    # Different devices prevent
                    # synthetic-device-ring detection.
                    "device_id":
                        f"SMURF_DEVICE_{i:04d}",

                    "device_type":
                        "mobile",

                    # Different IP addresses.
                    "ip_address":
                        f"10.0.0.{i + 10}",

                    # Structured amounts.
                    "amount":
                        round(
                            random.uniform(
                                4900,
                                4999,
                            ),
                            2,
                        ),

                    "transaction_type":
                        "TRANSFER",

                    "country":
                        "India",

                    "timestamp":
                        now_str,

                    # High velocity.
                    "seconds_since_prev":
                        8.0,

                    "velocity_1h":
                        450,

                    "attack_family":
                        "SMURFING",
                })

        # =====================================================
        # AI IMPERSONATION
        # =====================================================

        elif family == "AI_IMPERSONATION":

            txns.append({

                "transaction_id":
                    f"AI_IMP_{random.randint(100000, 999999)}",

                "user_id":
                    f"USER_{random.randint(1, 100):04d}",

                "amount":
                    round(
                        random.uniform(
                            45000,
                            85000,
                        ),
                        2,
                    ),

                "transaction_type":
                    "TRANSFER",

                "country":
                    "HighRisk_Offshore",

                "device_type":
                    "unknown",

                "device_id":
                    "AI_IMPERSONATION_DEVICE",

                "ip_address":
                    "45.33.32.156",

                "timestamp":
                    now_str,

                "seconds_since_prev":
                    3600.0,

                "velocity_1h":
                    1,

                "attack_family":
                    "AI_IMPERSONATION",
            })

        # =====================================================
        # ADAPTIVE MUTATION
        # =====================================================

        elif family == "ADAPTIVE_MUTATION":

            if mutation_context:

                base_amt = float(
                    mutation_context.get(
                        "amount",
                        85000.0,
                    )
                )

            else:

                base_amt = 85000.0

            mutated_amt = round(
                base_amt * 0.45,
                2,
            )

            txns.append({

                "transaction_id":
                    f"ADAPT_{random.randint(100000, 999999)}",

                "user_id":
                    f"USER_{random.randint(1, 100):04d}",

                "amount":
                    mutated_amt,

                "transaction_type":
                    "PAYMENT",

                "country":
                    "India",

                "device_type":
                    "mobile",

                "device_id":
                    "ADAPTIVE_DEVICE",

                "ip_address":
                    "103.21.244.2",

                "timestamp":
                    now_str,

                "seconds_since_prev":
                    450.0,

                "velocity_1h":
                    8,

                "attack_family":
                    "ADAPTIVE_MUTATION",
            })

        return txns