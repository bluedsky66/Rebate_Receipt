import json
import os
import random
import hashlib
from datetime import datetime
from us_rebate_receipts.src.models.core import (
    TargetSKU, GeneralSKU, RebateJobConfig, TaxRate, StoreLayoutConfig, ReceiptData
)
from us_rebate_receipts.src.engine.cart_builder import CartBuilder
from us_rebate_receipts.src.engine.tax_engine import TaxEngine
from us_rebate_receipts.src.engine.payment_matcher import PaymentMatcher
from us_rebate_receipts.src.engine.txn_lock import RegisterAwareTxnLock
from us_rebate_receipts.src.engine.sanity_checker import PreRenderSanityCheck
from us_rebate_receipts.src.engine.renderer import LayoutRenderer
from us_rebate_receipts.src.printers.printers import PngPrinter, DirectPrinter

# Load configs
def load_configs():
    with open("us_rebate_receipts/config/target_skus.json") as f:
        target_skus = [TargetSKU(**t) for t in json.load(f)["target_skus"]]

    with open("us_rebate_receipts/config/general_skus.json") as f:
        general_skus = [GeneralSKU(**g) for g in json.load(f)["general_skus"]]

    with open("us_rebate_receipts/config/tax_rates.json") as f:
        tax_rates = {k: TaxRate(**v) for k, v in json.load(f).items()}

    stores = ["walmart", "target", "costco", "cvs", "kroger", "walgreens"]
    layouts = {}
    tax_profiles = {}
    logo_paths = {}

    for store in stores:
        with open(f"us_rebate_receipts/config/stores/{store}/layout.json") as f:
            layouts[store] = StoreLayoutConfig(**json.load(f))
        with open(f"us_rebate_receipts/config/stores/{store}/tax_profile.json") as f:
            tax_profiles[store] = json.load(f)
        logo_paths[store] = f"us_rebate_receipts/config/stores/{store}/logo.png"

    return target_skus, general_skus, tax_rates, layouts, tax_profiles, logo_paths

def main():
    target_skus, general_skus, tax_rates, layouts, tax_profiles, logo_paths = load_configs()

    # Initialize Engines
    cart_builder = CartBuilder(target_skus, general_skus)
    tax_engine = TaxEngine(tax_rates, tax_profiles)
    payment_matcher = PaymentMatcher(layouts)
    txn_lock = RegisterAwareTxnLock()
    renderer = LayoutRenderer(layouts, logo_paths)

    # Create Job Config
    config = RebateJobConfig(
        target_skus=[target_skus[0].sku_id, target_skus[1].sku_id],
        filler_strategy="smart",
        filler_count_range=(4, 7),
        affinity_enforce=True,
        output_format="png",
        count=1
    )

    job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    batch_dir = f"us_rebate_receipts/output/{datetime.now().strftime('%Y-%m-%d')}_batch_001"

    png_printer = PngPrinter(batch_dir)
    direct_printer = DirectPrinter(batch_dir)

    print(f"Starting Job {job_id}...")

    for i in range(config.count):
        # 1. Build Cart
        cart = cart_builder.build_cart(config)

        # 2. Calculate Taxes
        cart = tax_engine.calculate_taxes(cart)

        # 3. Match Payment
        payment = payment_matcher.generate_payment(config, cart)

        # 4. Get Txn Lock
        # Pre-allocate VOID/RETURN
        register_id = random.choice(config.register_pool)

        if random.random() < config.void_ratio:
            txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "VOID", job_id)
        if random.random() < config.return_ratio:
            txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "RETURN", job_id)

        txn_seq, ts = txn_lock.next_seq(cart.store_id, register_id, job_id)

        # Format Timestamp
        layout = layouts[cart.store_id]
        ts_str = datetime.fromtimestamp(ts).strftime(layout.footer.time_format)

        receipt_data = ReceiptData(
            job_id=job_id,
            cart=cart,
            payment=payment,
            register_id=register_id,
            txn_seq=txn_seq,
            timestamp=ts_str
        )

        # 5. Sanity Check
        PreRenderSanityCheck.verify(receipt_data.cart, receipt_data.payment, config.affinity_enforce)

        # 6. Render and Print
        if config.output_format == "png":
            img = renderer.render_png(receipt_data)
            filename = f"receipt_{job_id}_{i:03d}.png"
            path = png_printer.print_receipt(img, filename)

            with open(path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

        else: # direct_print
            data = renderer.render_escpos(receipt_data)
            filename = f"direct_print_debug_{job_id}_{i:03d}.bin"
            path = direct_printer.print_receipt(data, filename)
            file_hash = hashlib.sha256(data).hexdigest()

        # Debug render ESCPOS for verification even when png
        data_debug = renderer.render_escpos(receipt_data)
        direct_printer.print_receipt(data_debug, f"direct_print_debug_{job_id}_{i:03d}.bin")

        txn_lock.update_transaction(cart.store_id, register_id, txn_seq, float(cart.total), file_hash)

        print(f"Generated {path}")

    print("Job complete.")

if __name__ == "__main__":
    main()
