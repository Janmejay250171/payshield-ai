import pandas as pd


class PaymentSimulator:
    def __init__(self, transactions):
        self.transactions = transactions.copy()

    def process_transaction(self, transaction_id):
        tx = self.transactions[
            self.transactions["transaction_id"] == transaction_id
        ]

        if tx.empty:
            raise ValueError("Transaction not found")

        return tx.iloc[0].to_dict()

    def get_transactions(self):
        return self.transactions.copy()


if __name__ == "__main__":
    df = pd.read_csv("data/raw/transactions.csv")

    simulator = PaymentSimulator(df)

    result = simulator.process_transaction("TXN00000001")

    print("Transaction processed:")
    print(result)