import json
import os
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

from utils.path_helper import get_base_dir, get_config_dir

def create_directory_structure():
    base_dir = get_base_dir()
    os.makedirs(base_dir / "config" / "stores", exist_ok=True)
    os.makedirs(base_dir / "jobs", exist_ok=True)
    os.makedirs(base_dir / "output", exist_ok=True)

NATIONAL_STORES = ["walmart", "target", "kroger", "safeway", "albertsons", "cost_plus", "sams_club", "total_wine", "walgreens", "exchange"]
FL_STORES = ["publix", "winn_dixie", "fresco_y_mas", "sedanos", "the_fresh_market", "sprouts", "milams", "hitchcocks", "rowes_iga", "abc_fine_wine", "crown_wine", "luekens_wine", "normans_liquors", "big_daddys", "mendez_fuel", "mega_liquors", "piggly_wiggly"]
OH_STORES = ["giant_eagle", "meijer", "heinens", "marcs", "discount_drug_mart", "buehlers", "daves_markets", "acme_fresh", "chief_supermarket", "community_markets", "jungle_jims", "arrow_wine", "minottis", "corkscrew_johnnys", "rozi_wine", "pat_obriens", "chateau_wine", "weilands"]
WY_STORES = ["ridleys", "smiths", "broulims", "blairs", "lynns", "town_country", "liquor_store_jackson", "basecamp", "star_liquors", "northstar_liquor", "keg_cork"]
OTHER_REGIONAL = ["cvs", "cub", "hy_vee", "jewel_osco", "pick_n_save", "woodmans", "discount_liquor", "empire_wine", "keyport_liquor", "lisas_liquor", "main_street_wine", "marketview_liquor", "premium_wine", "prestige_wine", "prime_wines", "yankee_spirits", "cash_wise", "coborns", "copps", "festival_foods", "gordys", "super_saver", "trigs"]

ALL_STORES = NATIONAL_STORES + FL_STORES + OH_STORES + WY_STORES + OTHER_REGIONAL

ALL_STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]

def get_store_regions(store_id):
    if store_id in NATIONAL_STORES:
        return ALL_STATES
    elif store_id in FL_STORES:
        return ["FL"]
    elif store_id in OH_STORES:
        return ["OH"]
    elif store_id in WY_STORES:
        return ["WY"]
    else:
        return ["IL", "WI", "MN", "NY", "MA"]

def generate_addresses(regions):
    addresses = {}
    cities = {
        "CA": [("LOS ANGELES", "90001"), ("SAN FRANCISCO", "94101"), ("SAN DIEGO", "92101"), ("SACRAMENTO", "95814"), ("FRESNO", "93721")],
        "TX": [("HOUSTON", "77001"), ("DALLAS", "75201"), ("AUSTIN", "73301"), ("SAN ANTONIO", "78205"), ("EL PASO", "78201")],
        "FL": [("MIAMI", "33101"), ("ORLANDO", "32801"), ("TAMPA", "33601"), ("FORT LAUDERDALE", "33306"), ("JACKSONVILLE", "32099")],
        "OH": [("COLUMBUS", "43201"), ("CLEVELAND", "44101"), ("CINCINNATI", "45201"), ("TOLEDO", "43601"), ("AKRON", "44301")],
        "WY": [("CHEYENNE", "82001"), ("CASPER", "82601"), ("JACKSON", "83001"), ("LARAMIE", "82070"), ("GILLETTE", "82716")],
        "NY": [("NEW YORK", "10001"), ("BUFFALO", "14201"), ("ALBANY", "12201"), ("SYRACUSE", "12202"), ("ROCHESTER", "14604")],
        "IL": [("CHICAGO", "60601"), ("SPRINGFIELD", "62701"), ("PEORIA", "61601"), ("NAPERVILLE", "60540"), ("ELGIN", "60120")]
    }

    for r in regions:
        addresses[r] = []
        for _ in range(random.randint(3, 5)):
            city_zip = random.choice(cities.get(r, [("CAPITAL", f"{random.randint(10000, 99999)}")]))
            store_num = str(random.randint(1000, 9999))
            addresses[r].append({
                "store_number": store_num,
                "street": f"{random.randint(100, 9999)} MAIN ST",
                "city": city_zip[0],
                "state": r,
                "zip": city_zip[1]
            })
    return addresses

def create_store_configs():
    config_dir = get_config_dir()
    for store in ALL_STORES:
        store_dir = config_dir / "stores" / store
        os.makedirs(store_dir, exist_ok=True)

        is_convenience = store in ["walgreens", "mendez_fuel", "abc_fine_wine", "crown_wine", "discount_drug_mart", "cvs"]
        is_detailed = store in ["walmart", "target", "costco", "sams_club", "albertsons", "kroger", "safeway", "publix", "sprouts", "the_fresh_market"]

        display_mode = "detailed" if is_detailed else ("compact" if is_convenience else "detailed")
        if is_convenience:
            line_height = 20
        elif store in ["walmart", "target", "costco", "sams_club"]:
            line_height = 30
        elif store in ["the_fresh_market", "sprouts"]:
            line_height = 26
        else:
            line_height = 24

        regions = get_store_regions(store)
        addresses = generate_addresses(regions)

        profile = {
            "store_id": store,
            "name": store.replace("_", " ").title() if store != "cvs" else "CVS",
            "region_whitelist": regions,
            "addresses": addresses,
            "layout_id": store,
            "logo_path": f"config/stores/{store}/logo.png",
            "tax_profile_id": store,
            "register_pool": ["01", "02", "03", "04", "05"],
            "register_mode": "random",
            "store_type": "convenience" if is_convenience else "standard"
        }
        with open(store_dir / "profile.json", "w") as f:
            json.dump(profile, f, indent=4)

        # Target specific logic
        mask_format = "{type} ****{last4}"
        if store == "target":
            mask_format = "TGT REDCARD ****{last4}"

        layout = {
            "store_id": store,
            "page_width_dots": 384,
            "line_height": line_height,
            "char_spacing": 0,
            "header": {
                "alignment": "center",
                "show_name": True,
                "show_address": True,
                "address_template": "#{store_number}\n{street}\n{city}, {state} {zip}"
            },
            "item_line": {
                "display_mode": display_mode,
                "name_align": "left",
                "price_align": "right",
                "price_offset": 0,
                "qty_template": "{qty} @ {unit_price}",
                "show_upc": store in ["walmart", "target"],
                "tax_indicator_taxable": "T",
                "tax_indicator_exempt": "F" if is_convenience else ""
            },
            "tax_line_format": {
                "mode": "split" if store in ["target", "publix", "ca"] else "single",
                "single_label": "TAX" if store == "walmart" else "TOTAL TAX",
                "split_labels": ["STATE TAX", "LOCAL TAX"],
                "show_rate": store == "walmart",
                "alignment": "right",
                "separator": " "
            },
            "payment_line": {
                "label": "TENDER",
                "alignment": "right",
                "mask_format": mask_format,
                "cash_label": "CASH",
                "store_specific": {
                    "walmart_pay": store == "walmart",
                    "walmart_pay_threshold": "100.00",
                    "costco_visa_only": store in ["costco", "sams_club"]
                },
                "payment_footer_lines": [
                    "APPROVED",
                    "CHANGE DUE {change}"
                ]
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
                "txn_format": "TC# {store_number}-{register}-{seq}\n{timestamp}",
                "show_time": True,
                "time_format": "%m/%d/%Y %I:%M:%S %p"
            },
            "custom_escpos": [
                "\x1b\x40",
                "\x1b\x61\x01"
            ]
        }
        with open(store_dir / "layout.json", "w") as f:
            json.dump(layout, f, indent=4)

        tax_profile = {
            "store_id": store,
            "mixed_rates": is_convenience,
            "tax_label_taxable": "T",
            "tax_label_exempt": "F" if is_convenience else ""
        }
        with open(store_dir / "tax_profile.json", "w") as f:
            json.dump(tax_profile, f, indent=4)

        color = (0, 113, 206) if store == "walmart" else ((204, 0, 0) if store in ["target", "cvs", "walgreens"] else (0, 0, 0))
        img = Image.new('RGB', (200, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.rectangle((20, 20, 180, 80), fill=color)
        d.text((50, 40), profile["name"][:12], fill=(255, 255, 255))
        img.save(store_dir / "logo.png")

def create_skus():
    target_skus = {
        "target_skus": [
            {
                "sku_id": "TIDE-PODS-42",
                "upc": "037000230687",
                "name": "Tide Pods Laundry Detergent Spring Meadow 42ct",
                "base_price": "12.99",
                "rebate_price": "12.99",
                "min_qty": 1,
                "valid_stores": NATIONAL_STORES,
                "valid_states": ALL_STATES,
                "category": "Household",
                "affinity_tags": ["laundry", "household_cleaning"],
                "weight": 100
            },
            {
                "sku_id": "PAMP-SWAD-4",
                "upc": "037000862246",
                "name": "Pampers Swaddlers Diapers Size 4 32ct",
                "base_price": "26.99",
                "rebate_price": "26.99",
                "min_qty": 1,
                "valid_stores": NATIONAL_STORES,
                "valid_states": ALL_STATES,
                "category": "Baby Care",
                "affinity_tags": ["baby_care", "diapers"],
                "weight": 100
            }
        ]
    }
    with open(get_config_dir() / "target_skus.json", "w") as f:
        json.dump(target_skus, f, indent=4)

    # General SKUs without any "Generic" logic, 120+ strictly realistic
    general_skus_list = []
    def add_skus(scene, items):
        for i, item in enumerate(items):
            general_skus_list.append({
                "sku_id": f"{scene.upper()}-{i+1}",
                "upc": f"800{random.randint(100000000, 999999999)}",
                "name": item[0],
                "base_price": f"{item[1]:.2f}",
                "category": "General",
                "affinity_tags": [scene],
                "weight": 50
            })

    add_skus("laundry", [
        ("Gain Flings Laundry Detergent Pacs 42ct", 12.99),
        ("All Mighty Pacs Laundry Detergent Free Clear 60ct", 14.99),
        ("Arm & Hammer Liquid Laundry Detergent Clean Burst 144oz", 9.99),
        ("Persil ProClean Liquid Laundry Detergent Original 100oz", 13.99),
        ("Purex Liquid Laundry Detergent Mountain Breeze 150oz", 8.99),
        ("OxiClean Versatile Stain Remover Powder 3lb", 7.99),
        ("Seventh Generation Liquid Laundry Detergent 100oz", 14.99),
        ("Bounce WrinkleGuard Mega Dryer Sheets 120ct", 9.99),
        ("Downy Unstopables Scent Booster Beads 14.8oz", 10.99),
        ("Suavitel Liquid Fabric Softener Field Flowers 120oz", 8.99),
        ("Snuggle Liquid Fabric Softener Blue Sparkle 96oz", 7.99),
        ("Gain Liquid Fabric Softener Original 164oz", 12.99)
    ])

    add_skus("fabric_care", [
        ("Downy Ultra Fabric Softener April Fresh 51oz", 5.99),
        ("Bounce Fabric Softener Sheets Outdoor Fresh 240ct", 9.99),
        ("Snuggle Fabric Softener Sheets Blue Sparkle 120ct", 4.99),
        ("Gain Dryer Sheets Original 240ct", 9.99),
        ("Downy Infusions Liquid Fabric Softener 32oz", 6.99),
        ("Clorox Fabric Sanitizer Spray 14oz", 5.99),
        ("Shout Triple-Acting Laundry Stain Remover Spray 22oz", 3.49),
        ("Resolve Spray Wash Pre-Treat Stain Remover 22oz", 3.99),
        ("Tide Rescue Laundry Stain Remover 22oz", 4.99),
        ("Carbona Color Run Remover 2.6oz", 3.29),
        ("Woolite Delicates Liquid Laundry Detergent 16oz", 5.99),
        ("Biz Stain Eliminator Powder 37.5oz", 6.99)
    ])

    add_skus("household_cleaning", [
        ("Clorox Disinfecting Bleach Regular 121oz", 6.99),
        ("Lysol Disinfectant Spray Crisp Linen 19oz", 7.49),
        ("Mr Clean Multi-Surface Cleaner 40oz", 4.49),
        ("Windex Glass Cleaner Original 23oz", 3.99),
        ("Pine-Sol Multi-Surface Cleaner Lemon Fresh 48oz", 4.99),
        ("Method All-Purpose Cleaner Pink Grapefruit 28oz", 4.49),
        ("Clorox Disinfecting Wipes Crisp Lemon 75ct", 5.99),
        ("Scrubbing Bubbles Bathroom Grime Fighter Citrus 20oz", 4.49),
        ("Soft Scrub Cleanser with Bleach 24oz", 3.99),
        ("Swiffer WetJet Multi-Purpose Cleaner Refill 42oz", 6.99),
        ("Pledge Everyday Clean Multi-Surface Cleaner Lemon 9.7oz", 5.49),
        ("Easy-Off Heavy Duty Oven Cleaner Regular 14.5oz", 4.99)
    ])

    add_skus("baby_care", [
        ("Johnsons Baby Shampoo Tear-Free 20.3oz", 5.99),
        ("Desitin Maximum Strength Baby Diaper Rash Cream 4oz", 7.99),
        ("Aquaphor Baby Healing Ointment 14oz", 16.99),
        ("Aveeno Baby Daily Moisture Lotion 18oz", 10.99),
        ("Boudreauxs Butt Paste Maximum Strength 4oz", 7.49),
        ("Baby Magic Gentle Baby Lotion Original 30oz", 6.99),
        ("Zarbees Naturals Baby Cough Syrup Grape 2oz", 8.99),
        ("FridaBaby NoseFrida The Snotsucker Nasal Aspirator", 16.99),
        ("WaterWipes Unscented Baby Wipes 240ct", 14.99),
        ("Huggies Natural Care Sensitive Baby Wipes 168ct", 6.99),
        ("Pampers Aqua Pure Sensitive Baby Wipes 112ct", 6.49),
        ("Hello Bello Plant-Based Baby Wipes 180ct", 8.99)
    ])

    add_skus("diapers", [
        ("Pampers Cruisers Diapers Size 5 52ct", 28.99),
        ("Huggies OverNites Diapers Size 4 58ct", 28.99),
        ("The Honest Company Clean Conscious Diapers Size 3 68ct", 29.99),
        ("Luvs Pro Level Leak Protection Diapers Size 4 74ct", 19.99),
        ("Seventh Generation Baby Diapers Size 3 60ct", 28.99),
        ("Huggies Little Movers Diapers Size 5 50ct", 28.99),
        ("Pampers Baby-Dry Diapers Size 6 42ct", 28.99),
        ("Hello Bello Premium Diapers Size 4 54ct", 23.99),
        ("Huggies Snug Dry Diapers Size 4 62ct", 24.99),
        ("Pampers Easy Ups Training Underwear Boys Size 4T 56ct", 28.99),
        ("Pull-Ups Boys Potty Training Pants Size 3T 66ct", 28.99),
        ("Goodnites Nighttime Bedwetting Underwear Girls Size L 34ct", 28.99)
    ])

    add_skus("snacks", [
        ("Oreo Chocolate Sandwich Cookies Family Size 19.1oz", 4.99),
        ("Ritz Crackers Original Family Size 20.5oz", 5.49),
        ("Cheez-It Baked Snack Crackers Original 21oz", 6.49),
        ("Goldfish Cheddar Crackers Family Size 27.3oz", 8.99),
        ("Nabisco Premium Saltine Crackers Original 16oz", 3.49),
        ("Keebler Club Crackers Original 13.7oz", 4.29),
        ("Wheat Thins Original Crackers Family Size 14oz", 5.49),
        ("Triscuit Original Crackers Family Size 12.5oz", 5.49),
        ("Pop-Tarts Frosted Strawberry Toaster Pastries 12ct", 4.49),
        ("Quaker Chewy Granola Bars Chocolate Chip 18ct", 5.99),
        ("Nature Valley Crunchy Granola Bars Honey 12ct", 4.29),
        ("Slim Jim Original Giant Smoked Meat Stick .97oz", 1.49)
    ])

    add_skus("chips", [
        ("Lays Classic Potato Chips Party Size 13oz", 5.99),
        ("Doritos Nacho Cheese Flavored Tortilla Chips 14.5oz", 5.99),
        ("Tostitos Scoops Tortilla Chips Party Size 14.5oz", 5.99),
        ("Cheetos Puffs Cheese Flavored Snacks Party Size 13.5oz", 5.99),
        ("Ruffles Original Potato Chips Party Size 13oz", 5.99),
        ("Fritos Original Corn Chips Party Size 15.5oz", 5.99),
        ("Pringles Sour Cream Onion Potato Crisps 5.5oz", 2.49),
        ("Cape Cod Original Kettle Cooked Potato Chips 8oz", 4.29),
        ("Kettle Brand Sea Salt Potato Chips 8.5oz", 4.29),
        ("Takis Fuego Rolled Tortilla Chips 9.9oz", 3.99),
        ("SunChips Harvest Cheddar Whole Grain Snacks 7oz", 4.29),
        ("Smartfood White Cheddar Popcorn 6.75oz", 4.29)
    ])

    add_skus("candy", [
        ("M&Ms Milk Chocolate Candies Sharing Size 10.7oz", 4.99),
        ("Reeses Peanut Butter Cups Milk Chocolate 6ct", 5.49),
        ("Snickers Chocolate Candy Bars 6ct", 5.49),
        ("Hersheys Milk Chocolate Candy Bars 6ct", 5.49),
        ("Twix Caramel Cookie Chocolate Candy Bars 6ct", 5.49),
        ("Kit Kat Milk Chocolate Wafer Candy Bars 6ct", 5.49),
        ("Skittles Original Fruity Candy Sharing Size 15.6oz", 4.99),
        ("Starburst Original Fruit Chews Candy Sharing Size 15.6oz", 4.99),
        ("Sour Patch Kids Soft Chewy Candy Sharing Size 14.4oz", 4.99),
        ("Swedish Fish Soft Chewy Candy Sharing Size 14.4oz", 4.99),
        ("Haribo Goldbears Gummi Candy 8oz", 2.99),
        ("Trolli Sour Brite Crawlers Gummi Worms 9oz", 2.99)
    ])

    add_skus("soda", [
        ("Coca-Cola Classic Cola 12 Pack 12oz Cans", 7.99),
        ("Diet Coke 12 Pack 12oz Cans", 7.99),
        ("Sprite Lemon-Lime Soda 12 Pack 12oz Cans", 7.99),
        ("Pepsi Cola 12 Pack 12oz Cans", 7.99),
        ("Diet Pepsi 12 Pack 12oz Cans", 7.99),
        ("Mountain Dew Citrus Soda 12 Pack 12oz Cans", 7.99),
        ("Dr Pepper Soda 12 Pack 12oz Cans", 7.99),
        ("Diet Dr Pepper Soda 12 Pack 12oz Cans", 7.99),
        ("AW Root Beer Soda 12 Pack 12oz Cans", 7.99),
        ("Canada Dry Ginger Ale 12 Pack 12oz Cans", 7.99),
        ("Sunkist Orange Soda 12 Pack 12oz Cans", 7.99),
        ("7UP Lemon Lime Soda 12 Pack 12oz Cans", 7.99)
    ])

    with open(get_config_dir() / "general_skus.json", "w") as f:
        json.dump({"general_skus": general_skus_list}, f, indent=4)

def create_tax_rates():
    tax_rates = {}
    for state in ALL_STATES:
        tax_rates[state] = {
            "state_code": state,
            "state_rate": "0.0600",
            "local_avg": "0.0150",
            "food_exempt": True if state not in ["AL", "ID", "MO"] else False,
            "split_tax": state in ["CA", "NY"]
        }
    with open(get_config_dir() / "tax_rates.json", "w") as f:
        json.dump(tax_rates, f, indent=4)

if __name__ == "__main__":
    create_directory_structure()
    create_store_configs()
    create_tax_rates()
    create_skus()
    print("Configs fully regenerated inside config/ properly without nesting.")
