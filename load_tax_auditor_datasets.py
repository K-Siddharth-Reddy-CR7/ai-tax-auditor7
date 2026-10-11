import pandas as pd

products = pd.read_csv("products.csv")
taxes = pd.read_csv("taxes.csv")
policies = pd.read_csv("trade_policies.csv")
transactions = pd.read_csv("sample_transactions.csv")

print("Products:", len(products))
print("Countries:", len(taxes))
print("Policies:", len(policies))
print("Transactions:", len(transactions))
