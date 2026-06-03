import json

with open("us_rebate_receipts/config/tax_rates.json", "r") as f:
    tax_rates = json.load(f)

tax_rates["IL"] = {
    "state_code": "IL",
    "state_rate": "0.0625",
    "local_avg": "0.0250",
    "food_exempt": False,
    "split_tax": False
}

with open("us_rebate_receipts/config/tax_rates.json", "w") as f:
    json.dump(tax_rates, f, indent=4)
