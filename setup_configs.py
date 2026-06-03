import json
import os
from PIL import Image, ImageDraw, ImageFont

def create_directory_structure():
    base_dir = "us_rebate_receipts"
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/walmart", exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/target", exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/costco", exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/cvs", exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/kroger", exist_ok=True)
    os.makedirs(f"{base_dir}/config/stores/walgreens", exist_ok=True)
    os.makedirs(f"{base_dir}/jobs", exist_ok=True)
    os.makedirs(f"{base_dir}/output", exist_ok=True)
    os.makedirs(f"{base_dir}/src/models", exist_ok=True)
    os.makedirs(f"{base_dir}/src/engine", exist_ok=True)
    os.makedirs(f"{base_dir}/src/gui", exist_ok=True)
    os.makedirs(f"{base_dir}/src/printers", exist_ok=True)
    os.makedirs(f"{base_dir}/tests", exist_ok=True)

def create_target_skus():
    target_skus = {
        "target_skus": [
            {
                "sku_id": "TSKU-001",
                "upc": "037000230687",
                "name": "Tide Liquid Laundry Detergent",
                "base_price": "12.99",
                "rebate_price": "12.99",
                "min_qty": 1,
                "valid_stores": ["walmart", "target", "costco", "cvs", "kroger", "walgreens"],
                "valid_states": ["CA", "TX", "NY", "FL", "IL"],
                "category": "Household",
                "affinity_tags": ["laundry", "household_cleaning"],
                "weight": 100
            },
            {
                "sku_id": "TSKU-002",
                "upc": "037000862246",
                "name": "Pampers Swaddlers Diapers",
                "base_price": "26.99",
                "rebate_price": "26.99",
                "min_qty": 1,
                "valid_stores": ["walmart", "target", "costco", "cvs", "kroger", "walgreens"],
                "valid_states": ["CA", "TX", "NY", "FL", "IL"],
                "category": "Baby Care",
                "affinity_tags": ["baby_care", "diapers"],
                "weight": 100
            },
            {
                "sku_id": "TSKU-003",
                "upc": "049000028904",
                "name": "Coca-Cola 12 Pack Cans",
                "base_price": "6.99",
                "rebate_price": "6.99",
                "min_qty": 2,
                "valid_stores": ["walmart", "target", "kroger", "cvs", "walgreens"],
                "valid_states": ["CA", "TX", "NY", "FL", "IL"],
                "category": "Beverages",
                "affinity_tags": ["beverages", "soda"],
                "weight": 100
            },
            {
                "sku_id": "TSKU-004",
                "upc": "028400589864",
                "name": "Lay's Classic Potato Chips",
                "base_price": "4.29",
                "rebate_price": "4.29",
                "min_qty": 1,
                "valid_stores": ["walmart", "target", "kroger", "cvs", "walgreens"],
                "valid_states": ["CA", "TX", "NY", "FL", "IL"],
                "category": "Snacks",
                "affinity_tags": ["snacks", "chips"],
                "weight": 100
            },
            {
                "sku_id": "TSKU-005",
                "upc": "011110428522",
                "name": "Kroger Large Eggs, 12 ct",
                "base_price": "2.49",
                "rebate_price": "2.49",
                "min_qty": 1,
                "valid_stores": ["kroger"],
                "valid_states": ["CA", "TX", "NY", "FL", "IL"],
                "category": "Dairy",
                "affinity_tags": ["dairy", "produce"],
                "weight": 100
            }
        ]
    }
    with open("us_rebate_receipts/config/target_skus.json", "w") as f:
        json.dump(target_skus, f, indent=4)

def create_general_skus():
    general_skus = {"general_skus": []}

    # 8 distinct scenes with ~10 items each

    # Scene 1: laundry, fabric_care, household_cleaning
    for i in range(1, 11):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-LAUNDRY-{i:03d}",
            "upc": f"100000000{i:03d}",
            "name": f"Generic Fabric Softener {i}",
            "base_price": f"{4.99 + i * 0.50:.2f}",
            "category": "Household",
            "affinity_tags": ["laundry", "fabric_care", "household_cleaning"],
            "weight": 50
        })

    # Scene 2: baby_care, diapers, wipes, baby_food
    for i in range(1, 11):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-BABY-{i:03d}",
            "upc": f"200000000{i:03d}",
            "name": f"Generic Baby Wipes {i}",
            "base_price": f"{2.99 + i * 0.25:.2f}",
            "category": "Baby Care",
            "affinity_tags": ["baby_care", "wipes"],
            "weight": 50
        })

    # Scene 3: snacks, chips, candy, soda
    for i in range(1, 15):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-SNACK-{i:03d}",
            "upc": f"300000000{i:03d}",
            "name": f"Generic Candy Bar {i}",
            "base_price": f"{1.50 + i * 0.10:.2f}",
            "category": "Snacks",
            "affinity_tags": ["snacks", "candy"],
            "weight": 70
        })

    # Scene 4: produce, dairy, frozen, beverages
    for i in range(1, 15):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-FOOD-{i:03d}",
            "upc": f"400000000{i:03d}",
            "name": f"Generic Frozen Pizza {i}",
            "base_price": f"{5.99 + i * 0.50:.2f}",
            "category": "Frozen",
            "affinity_tags": ["frozen", "produce", "dairy"],
            "weight": 60
        })

    # Scene 5: electronics, batteries, cables
    for i in range(1, 11):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-ELEC-{i:03d}",
            "upc": f"500000000{i:03d}",
            "name": f"Generic AA Batteries {i}",
            "base_price": f"{8.99 + i * 1.00:.2f}",
            "category": "Electronics",
            "affinity_tags": ["electronics", "batteries"],
            "weight": 30
        })

    # Scene 6: pharmacy, health, vitamins
    for i in range(1, 11):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-PHARM-{i:03d}",
            "upc": f"600000000{i:03d}",
            "name": f"Generic Multivitamin {i}",
            "base_price": f"{12.99 + i * 0.50:.2f}",
            "category": "Health",
            "affinity_tags": ["pharmacy", "health", "vitamins"],
            "weight": 40
        })

    # Scene 7: personal_care, shampoo, soap
    for i in range(1, 15):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-PCARE-{i:03d}",
            "upc": f"700000000{i:03d}",
            "name": f"Generic Shampoo {i}",
            "base_price": f"{6.99 + i * 0.20:.2f}",
            "category": "Personal Care",
            "affinity_tags": ["personal_care", "shampoo", "soap"],
            "weight": 60
        })

    # Scene 8: jewelry, accessories (for negative testing)
    for i in range(1, 6):
        general_skus["general_skus"].append({
            "sku_id": f"GSKU-JEWEL-{i:03d}",
            "upc": f"800000000{i:03d}",
            "name": f"Diamond Ring {i}",
            "base_price": f"{499.99 + i * 100:.2f}",
            "category": "Jewelry",
            "affinity_tags": ["jewelry", "accessories"],
            "weight": 5
        })

    with open("us_rebate_receipts/config/general_skus.json", "w") as f:
        json.dump(general_skus, f, indent=4)

def create_tax_rates():
    tax_rates = {
        "CA": {
            "state_code": "CA",
            "state_rate": "0.0725",
            "local_avg": "0.0150",
            "food_exempt": True,
            "split_tax": True
        },
        "TX": {
            "state_code": "TX",
            "state_rate": "0.0625",
            "local_avg": "0.0200",
            "food_exempt": True,
            "split_tax": False
        },
        "NY": {
            "state_code": "NY",
            "state_rate": "0.0400",
            "local_avg": "0.04875",
            "food_exempt": True,
            "split_tax": False
        },
        "FL": {
            "state_code": "FL",
            "state_rate": "0.0600",
            "local_avg": "0.0100",
            "food_exempt": True,
            "split_tax": False
        },
        "OR": {
            "state_code": "OR",
            "state_rate": "0.0000",
            "local_avg": "0.0000",
            "food_exempt": True,
            "split_tax": False
        }
    }
    with open("us_rebate_receipts/config/tax_rates.json", "w") as f:
        json.dump(tax_rates, f, indent=4)

def create_store_configs():
    stores = ["walmart", "target", "costco", "cvs", "kroger", "walgreens"]

    for store in stores:
        # Profile
        profile = {
            "store_id": store,
            "name": store.capitalize()
        }
        with open(f"us_rebate_receipts/config/stores/{store}/profile.json", "w") as f:
            json.dump(profile, f, indent=4)

        # Layout (stubs for others, complete for walmart/target)
        layout = {
            "store_id": store,
            "page_width_dots": 384,
            "line_height": 30 if store == "walmart" else 26,
            "char_spacing": 0,
            "header": {
                "alignment": "center",
                "show_name": True,
                "show_address": True,
                "address_template": "123 MAIN ST\nCITY, STATE 12345"
            },
            "item_line": {
                "name_align": "left",
                "price_align": "right",
                "price_offset": 0,
                "qty_template": "{qty} @ {unit_price}",
                "show_upc": True if store == "walmart" else False
            },
            "tax_line_format": {
                "mode": "split" if store == "target" else "single",
                "single_label": "TAX" if store == "walmart" else "TOTAL TAX",
                "split_labels": ["STATE TAX", "LOCAL TAX"],
                "show_rate": True if store == "walmart" else False,
                "alignment": "right",
                "separator": " "
            },
            "payment_line": {
                "label": "TENDER",
                "alignment": "right",
                "mask_format": "{type} ****{last4}",
                "cash_label": "CASH",
                "store_specific": {
                    "walmart_pay": True if store == "walmart" else False,
                    "walmart_pay_threshold": "100.00",
                    "costco_visa_only": True if store == "costco" else False
                }
            },
            "total_section": {
                "subtotal_label": "SUBTOTAL",
                "tax_label": "TAX",
                "total_label": "TOTAL",
                "separator": "-" * 32
            },
            "footer": {
                "barcode_type": "CODE39",
                "terminal_id_format": "TERM {register}",
                "txn_format": "TC# {store_id} {register} {seq} {timestamp}",
                "show_time": True,
                "time_format": "%m/%d/%Y %H:%M:%S"
            },
            "custom_escpos": [
                "\x1b\x40", # Initialize
                "\x1b\x61\x01" # Center align
            ]
        }
        with open(f"us_rebate_receipts/config/stores/{store}/layout.json", "w") as f:
            json.dump(layout, f, indent=4)

        # Tax Profile
        tax_profile = {
            "store_id": store,
            "mixed_rates": True if store in ["cvs", "walgreens"] else False,
            "tax_label_taxable": "T",
            "tax_label_exempt": "F" if store in ["cvs", "walgreens"] else "N"
        }
        with open(f"us_rebate_receipts/config/stores/{store}/tax_profile.json", "w") as f:
            json.dump(tax_profile, f, indent=4)

        # Logo placeholder
        img = Image.new('RGB', (200, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((50, 40), store.capitalize(), fill=(0, 0, 0))
        img.save(f"us_rebate_receipts/config/stores/{store}/logo.png")

if __name__ == "__main__":
    create_directory_structure()
    create_target_skus()
    create_general_skus()
    create_tax_rates()
    create_store_configs()
    print("Configuration generation complete.")
