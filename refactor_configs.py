import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

def create_directory_structure():
    base_dir = "us_rebate_receipts"
    os.makedirs(base_dir, exist_ok=True)
    for folder in ["stores", "jobs", "output", "src/models", "src/engine", "src/gui", "src/printers", "tests"]:
        os.makedirs(f"{base_dir}/{folder}", exist_ok=True)

# Define store types
NATIONAL_STORES = ["walmart", "target", "kroger", "safeway", "albertsons", "cost_plus", "sams_club", "total_wine", "walgreens", "exchange"]
FL_STORES = ["publix", "winn_dixie", "fresco_y_mas", "sedanos", "the_fresh_market", "sprouts", "milams", "hitchcocks", "rowes_iga", "abc_fine_wine", "crown_wine", "luekens_wine", "normans_liquors", "big_daddys", "mendez_fuel", "mega_liquors", "piggly_wiggly"]
OH_STORES = ["giant_eagle", "meijer", "heinens", "marcs", "discount_drug_mart", "buehlers", "daves_markets", "acme_fresh", "chief_supermarket", "community_markets", "jungle_jims", "arrow_wine", "minottis", "corkscrew_johnnys", "rozi_wine", "pat_obriens", "chateau_wine", "weilands"]
WY_STORES = ["ridleys", "smiths", "broulims", "blairs", "lynns", "town_country", "liquor_store_jackson", "basecamp", "star_liquors", "northstar_liquor", "keg_cork"]
OTHER_REGIONAL = ["cub", "hy_vee", "jewel_osco", "pick_n_save", "woodmans", "discount_liquor", "empire_wine", "keyport_liquor", "lisas_liquor", "main_street_wine", "marketview_liquor", "premium_wine", "prestige_wine", "prime_wines", "yankee_spirits", "cash_wise", "coborns", "copps", "festival_foods", "gordys", "super_saver", "trigs"]

ALL_STORES = NATIONAL_STORES + FL_STORES + OH_STORES + WY_STORES + OTHER_REGIONAL

def get_store_regions(store_id):
    if store_id in NATIONAL_STORES:
        return ["CA", "TX", "FL", "OH", "WY", "NY", "IL", "AZ", "OR"]
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
        "CA": [("LOS ANGELES", "90001"), ("SAN FRANCISCO", "94101"), ("SAN DIEGO", "92101")],
        "TX": [("HOUSTON", "77001"), ("DALLAS", "75201"), ("AUSTIN", "73301")],
        "FL": [("MIAMI", "33101"), ("ORLANDO", "32801"), ("TAMPA", "33601"), ("FORT LAUDERDALE", "33306")],
        "OH": [("COLUMBUS", "43201"), ("CLEVELAND", "44101"), ("CINCINNATI", "45201")],
        "WY": [("CHEYENNE", "82001"), ("CASPER", "82601"), ("JACKSON", "83001")],
        "NY": [("NEW YORK", "10001"), ("BUFFALO", "14201"), ("ALBANY", "12201")],
        "IL": [("CHICAGO", "60601"), ("SPRINGFIELD", "62701"), ("PEORIA", "61601")],
        "AZ": [("PHOENIX", "85001"), ("TUCSON", "85701"), ("MESA", "85201")],
        "OR": [("PORTLAND", "97201"), ("SALEM", "97301"), ("EUGENE", "97401")],
        "WI": [("MILWAUKEE", "53201")],
        "MN": [("MINNEAPOLIS", "55401")],
        "MA": [("BOSTON", "02101")]
    }
    for r in regions:
        addresses[r] = []
        for _ in range(random.randint(2, 5)):
            city_zip = random.choice(cities.get(r, [("CITY", "00000")]))
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
    # Make stores directory
    os.makedirs("us_rebate_receipts/config/stores", exist_ok=True)

    for store in ALL_STORES:
        os.makedirs(f"us_rebate_receipts/config/stores/{store}", exist_ok=True)

        # Determine store type for logic
        is_convenience = store in ["walgreens", "mendez_fuel", "abc_fine_wine", "crown_wine", "discount_drug_mart"]
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
            "name": store.replace("_", " ").title(),
            "region_whitelist": regions,
            "addresses": addresses,
            "layout_id": store,
            "logo_path": f"us_rebate_receipts/config/stores/{store}/logo.png",
            "tax_profile_id": store,
            "register_pool": ["01", "02", "03", "04", "05"],
            "register_mode": "random",
            "store_type": "convenience" if is_convenience else "standard"
        }
        with open(f"us_rebate_receipts/config/stores/{store}/profile.json", "w") as f:
            json.dump(profile, f, indent=4)

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
                "tax_indicator_exempt": "F" if store in ["cvs", "walgreens"] else ""
            },
            "tax_line_format": {
                "mode": "split" if store in ["target", "publix"] else "single",
                "single_label": "TAX" if store == "walmart" else "TOTAL TAX",
                "split_labels": ["STATE TAX", "LOCAL TAX"],
                "show_rate": store == "walmart",
                "alignment": "right",
                "separator": " "
            },
            "payment_line": {
                "label": "TENDER",
                "alignment": "right",
                "mask_format": "{type} ****{last4}",
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
                "\x1b\x40", # Initialize
                "\x1b\x61\x01" # Center align
            ]
        }
        with open(f"us_rebate_receipts/config/stores/{store}/layout.json", "w") as f:
            json.dump(layout, f, indent=4)

        tax_profile = {
            "store_id": store,
            "mixed_rates": is_convenience,
            "tax_label_taxable": "T",
            "tax_label_exempt": "F" if is_convenience else ""
        }
        with open(f"us_rebate_receipts/config/stores/{store}/tax_profile.json", "w") as f:
            json.dump(tax_profile, f, indent=4)

        # Logo placeholder
        color = (0, 113, 206) if store == "walmart" else ((204, 0, 0) if store in ["target", "walgreens"] else (0, 0, 0))
        img = Image.new('RGB', (200, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.rectangle((20, 20, 180, 80), fill=color)
        d.text((50, 40), profile["name"][:12], fill=(255, 255, 255))
        img.save(f"us_rebate_receipts/config/stores/{store}/logo.png")

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
                "valid_states": ["CA", "TX", "FL", "OH", "WY", "NY", "IL", "AZ", "OR"],
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
                "valid_states": ["CA", "TX", "FL", "OH", "WY", "NY", "IL", "AZ", "OR"],
                "category": "Baby Care",
                "affinity_tags": ["baby_care", "diapers"],
                "weight": 100
            },
            {
                "sku_id": "COKE-12PK",
                "upc": "049000028904",
                "name": "Coca-Cola Classic Cola 12 Pack 12oz Cans",
                "base_price": "6.99",
                "rebate_price": "6.99",
                "min_qty": 2,
                "valid_stores": NATIONAL_STORES + FL_STORES + OH_STORES,
                "valid_states": ["CA", "TX", "FL", "OH", "WY", "NY", "IL", "AZ", "OR"],
                "category": "Beverages",
                "affinity_tags": ["beverages", "soda"],
                "weight": 100
            },
            {
                "sku_id": "LAY-CLASSIC-8",
                "upc": "028400589864",
                "name": "Lay's Classic Potato Chips 8oz Bag",
                "base_price": "4.29",
                "rebate_price": "4.29",
                "min_qty": 1,
                "valid_stores": NATIONAL_STORES + FL_STORES + OH_STORES,
                "valid_states": ["CA", "TX", "FL", "OH", "WY", "NY", "IL", "AZ", "OR"],
                "category": "Snacks",
                "affinity_tags": ["snacks", "chips"],
                "weight": 100
            },
            {
                "sku_id": "KROGER-EGGS-12",
                "upc": "011110428522",
                "name": "Kroger Large Grade A Eggs 12ct",
                "base_price": "2.49",
                "rebate_price": "2.49",
                "min_qty": 1,
                "valid_stores": ["kroger", "ralphs", "smiths", "frys"],
                "valid_states": ["CA", "TX", "OH", "WY"],
                "category": "Dairy",
                "affinity_tags": ["dairy", "produce"],
                "weight": 100
            }
        ]
    }
    with open("us_rebate_receipts/config/target_skus.json", "w") as f:
        json.dump(target_skus, f, indent=4)

    # General SKUs
    general_skus_list = []

    # helper
    def add_skus(scene, items):
        nonlocal general_skus_list
        for i, item in enumerate(items):
            general_skus_list.append({
                "sku_id": f"G-{scene.upper()}-{i+1}",
                "upc": f"800{random.randint(100000000, 999999999)}",
                "name": item[0],
                "base_price": f"{item[1]:.2f}",
                "category": "General",
                "affinity_tags": [scene],
                "weight": 50
            })

    # laundry
    add_skus("laundry", [
        ("Gain Flings Liquid Laundry Detergent Pacs Original 42ct", 12.99),
        ("All Mighty Pacs Laundry Detergent Free Clear 60ct", 14.99),
        ("Arm & Hammer Liquid Laundry Detergent Clean Burst 144oz", 9.99),
        ("Persil ProClean Liquid Laundry Detergent Original 100oz", 13.99),
        ("Purex Liquid Laundry Detergent Mountain Breeze 150oz", 8.99),
        ("OxiClean Versatile Stain Remover Powder 3lb", 7.99),
        ("Seventh Generation Liquid Laundry Detergent Free & Clear 100oz", 14.99),
        ("Bounce WrinkleGuard Mega Dryer Sheets Outdoor Fresh 120ct", 9.99),
        ("Downy Unstopables In-Wash Scent Booster Beads Fresh 14.8oz", 10.99),
        ("Suavitel Liquid Fabric Softener Field Flowers 120oz", 8.99),
        ("Snuggle Liquid Fabric Softener Blue Sparkle 96oz", 7.99),
        ("Gain Liquid Fabric Softener Original 164oz", 12.99)
    ])

    # fabric_care
    add_skus("fabric_care", [
        ("Downy Ultra Fabric Softener April Fresh 51oz", 5.99),
        ("Bounce Fabric Softener Sheets Outdoor Fresh 240ct", 9.99),
        ("Snuggle Fabric Softener Sheets Blue Sparkle 120ct", 4.99),
        ("Gain Dryer Sheets Original 240ct", 9.99),
        ("Downy Infusions Liquid Fabric Softener Calm Lavender 32oz", 6.99),
        ("Clorox Fabric Sanitizer Spray 14oz", 5.99),
        ("Shout Triple-Acting Laundry Stain Remover Spray 22oz", 3.49),
        ("Resolve Spray 'n Wash Pre-Treat Stain Remover 22oz", 3.99),
        ("Tide Rescue Laundry Stain Remover 22oz", 4.99),
        ("Carbona Color Run Remover 2.6oz", 3.29),
        ("Woolite Delicates Hypoallergenic Liquid Laundry Detergent 16oz", 5.99),
        ("Biz Stain & Odor Eliminator Powder 37.5oz", 6.99)
    ])

    # household_cleaning
    add_skus("household_cleaning", [
        ("Clorox Disinfecting Bleach Regular 121oz", 6.99),
        ("Lysol Disinfectant Spray Crisp Linen 19oz", 7.49),
        ("Mr. Clean Multi-Surface Cleaner Meadows & Rain 40oz", 4.49),
        ("Windex Glass Cleaner Original 23oz", 3.99),
        ("Pine-Sol Multi-Surface Cleaner Lemon Fresh 48oz", 4.99),
        ("Method All-Purpose Cleaner Pink Grapefruit 28oz", 4.49),
        ("Clorox Disinfecting Wipes Crisp Lemon 75ct", 5.99),
        ("Scrubbing Bubbles Bathroom Grime Fighter Citrus 20oz", 4.49),
        ("Soft Scrub All Purpose Cleanser with Bleach 24oz", 3.99),
        ("Swiffer WetJet Multi-Purpose Cleaner Refill Open Window Fresh 42oz", 6.99),
        ("Pledge Everyday Clean Multi-Surface Cleaner Lemon 9.7oz", 5.49),
        ("Easy-Off Heavy Duty Oven Cleaner Regular 14.5oz", 4.99)
    ])

    # baby_care
    add_skus("baby_care", [
        ("Johnson's Baby Shampoo Tear-Free 20.3oz", 5.99),
        ("Desitin Maximum Strength Baby Diaper Rash Cream 4oz", 7.99),
        ("Aquaphor Baby Healing Ointment 14oz", 16.99),
        ("Aveeno Baby Daily Moisture Lotion 18oz", 10.99),
        ("Boudreaux's Butt Paste Maximum Strength 4oz", 7.49),
        ("Baby Magic Gentle Baby Lotion Original 30oz", 6.99),
        ("Zarbee's Naturals Baby Cough Syrup Grape 2oz", 8.99),
        ("FridaBaby NoseFrida The Snotsucker Nasal Aspirator", 16.99),
        ("WaterWipes Unscented Baby Wipes 240ct", 14.99),
        ("Huggies Natural Care Sensitive Baby Wipes 168ct", 6.99),
        ("Pampers Aqua Pure Sensitive Baby Wipes 112ct", 6.49),
        ("Hello Bello Plant-Based Baby Wipes 180ct", 8.99)
    ])

    # diapers
    add_skus("diapers", [
        ("Pampers Cruisers Diapers Size 5 52ct", 28.99),
        ("Huggies OverNites Diapers Size 4 58ct", 28.99),
        ("The Honest Company Clean Conscious Diapers Size 3 68ct", 29.99),
        ("Luvs Pro Level Leak Protection Diapers Size 4 74ct", 19.99),
        ("Seventh Generation Baby Diapers Size 3 60ct", 28.99),
        ("Huggies Little Movers Diapers Size 5 50ct", 28.99),
        ("Pampers Baby-Dry Diapers Size 6 42ct", 28.99),
        ("Hello Bello Premium Diapers Size 4 54ct", 23.99),
        ("Huggies Snug & Dry Diapers Size 4 62ct", 24.99),
        ("Pampers Easy Ups Training Underwear Boys Size 4T-5T 56ct", 28.99),
        ("Pull-Ups Boys Potty Training Pants Size 3T-4T 66ct", 28.99),
        ("Goodnites Nighttime Bedwetting Underwear Girls Size L 34ct", 28.99)
    ])

    # snacks
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
        ("Nature Valley Crunchy Granola Bars Oats 'n Honey 12ct", 4.29),
        ("Slim Jim Original Giant Smoked Meat Stick .97oz", 1.49)
    ])

    # chips
    add_skus("chips", [
        ("Lay's Classic Potato Chips Party Size 13oz", 5.99),
        ("Doritos Nacho Cheese Flavored Tortilla Chips Party Size 14.5oz", 5.99),
        ("Tostitos Scoops! Tortilla Chips Party Size 14.5oz", 5.99),
        ("Cheetos Puffs Cheese Flavored Snacks Party Size 13.5oz", 5.99),
        ("Ruffles Original Potato Chips Party Size 13oz", 5.99),
        ("Fritos Original Corn Chips Party Size 15.5oz", 5.99),
        ("Pringles Sour Cream & Onion Potato Crisps 5.5oz", 2.49),
        ("Cape Cod Original Kettle Cooked Potato Chips 8oz", 4.29),
        ("Kettle Brand Sea Salt Potato Chips 8.5oz", 4.29),
        ("Takis Fuego Rolled Tortilla Chips 9.9oz", 3.99),
        ("SunChips Harvest Cheddar Whole Grain Snacks 7oz", 4.29),
        ("Smartfood White Cheddar Popcorn 6.75oz", 4.29)
    ])

    # candy
    add_skus("candy", [
        ("M&M's Milk Chocolate Candies Sharing Size 10.7oz", 4.99),
        ("Reese's Peanut Butter Cups Milk Chocolate 6ct", 5.49),
        ("Snickers Chocolate Candy Bars 6ct", 5.49),
        ("Hershey's Milk Chocolate Candy Bars 6ct", 5.49),
        ("Twix Caramel Cookie Chocolate Candy Bars 6ct", 5.49),
        ("Kit Kat Milk Chocolate Wafer Candy Bars 6ct", 5.49),
        ("Skittles Original Fruity Candy Sharing Size 15.6oz", 4.99),
        ("Starburst Original Fruit Chews Candy Sharing Size 15.6oz", 4.99),
        ("Sour Patch Kids Soft & Chewy Candy Sharing Size 14.4oz", 4.99),
        ("Swedish Fish Soft & Chewy Candy Sharing Size 14.4oz", 4.99),
        ("Haribo Goldbears Gummi Candy 8oz", 2.99),
        ("Trolli Sour Brite Crawlers Gummi Worms 9oz", 2.99)
    ])

    # soda
    add_skus("soda", [
        ("Coca-Cola Classic 12 Pack 12oz Cans", 7.99),
        ("Diet Coke 12 Pack 12oz Cans", 7.99),
        ("Sprite Lemon-Lime Soda 12 Pack 12oz Cans", 7.99),
        ("Pepsi Cola 12 Pack 12oz Cans", 7.99),
        ("Diet Pepsi 12 Pack 12oz Cans", 7.99),
        ("Mountain Dew Citrus Soda 12 Pack 12oz Cans", 7.99),
        ("Dr Pepper Soda 12 Pack 12oz Cans", 7.99),
        ("Diet Dr Pepper Soda 12 Pack 12oz Cans", 7.99),
        ("A&W Root Beer Soda 12 Pack 12oz Cans", 7.99),
        ("Canada Dry Ginger Ale 12 Pack 12oz Cans", 7.99),
        ("Sunkist Orange Soda 12 Pack 12oz Cans", 7.99),
        ("7UP Lemon Lime Soda 12 Pack 12oz Cans", 7.99)
    ])

    # dairy
    add_skus("dairy", [
        ("Prairie Farms Whole Milk 1 Gallon", 3.99),
        ("Kraft Shredded Sharp Cheddar Cheese 8oz", 3.49),
        ("Sargento Sliced Provolone Cheese 11ct", 3.99),
        ("Philadelphia Original Cream Cheese 8oz", 3.49),
        ("Chobani Non-Fat Greek Yogurt Strawberry 5.3oz", 1.29),
        ("Yoplait Original Yogurt Strawberry 6oz", 0.89),
        ("Land O Lakes Unsalted Butter 16oz", 5.99),
        ("Daisy Pure & Natural Sour Cream 16oz", 2.49),
        ("International Delight French Vanilla Creamer 32oz", 3.99),
        ("Silk Unsweetened Almondmilk 64oz", 3.49),
        ("Fairlife 2% Reduced Fat Ultra-Filtered Milk 52oz", 4.49),
        ("Reddi-wip Original Dairy Whipped Topping 6.5oz", 3.29)
    ])

    # produce
    add_skus("produce", [
        ("Fresh Bananas 1 Bunch", 1.89),
        ("Gala Apples 3lb Bag", 4.99),
        ("Navel Oranges 3lb Bag", 5.99),
        ("Fresh Strawberries 1lb", 3.99),
        ("Fresh Blueberries 1dry pint", 4.99),
        ("Hass Avocados 4ct Bag", 5.49),
        ("Roma Tomatoes 1lb", 1.99),
        ("Yellow Onions 3lb Bag", 3.49),
        ("Russet Potatoes 5lb Bag", 4.49),
        ("Fresh Express Iceberg Garden Salad 12oz", 2.49),
        ("Grimmway Farms Baby Carrots 1lb Bag", 1.49),
        ("Fresh Broccoli Crowns 1lb", 2.29)
    ])

    with open("us_rebate_receipts/config/general_skus.json", "w") as f:
        json.dump({"general_skus": general_skus_list}, f, indent=4)

if __name__ == "__main__":
    create_directory_structure()
    create_store_configs()
    create_skus()
    print("Configs fully regenerated.")
