#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 入口文件
用法: python main.py
"""

import sys
import os
import random
import hashlib
from datetime import datetime
from pathlib import Path

# Ensure src is in sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

from models.core import (
    TargetSKU, GeneralSKU, RebateJobConfig, TaxRate, StoreLayoutConfig, ReceiptData, StoreProfileConfig
)
from engine.cart_builder import CartBuilder
from engine.tax_engine import TaxEngine
from engine.payment_matcher import PaymentMatcher
from engine.txn_lock import RegisterAwareTxnLock
from engine.sanity_checker import PreRenderSanityCheck
from engine.renderer import LayoutRenderer
from printers.printers import PngPrinter, DirectPrinter
from utils.config_loader import ConfigLoader
from utils.path_helper import get_store_logo_path, get_config_dir
from utils.output_helper import get_next_batch_dir

# Load configs
def load_configs_main():
    target_data = ConfigLoader.load_json("target_skus.json")
    target_skus = [TargetSKU(**t) for t in target_data["target_skus"]]

    general_data = ConfigLoader.load_json("general_skus.json")
    general_skus = [GeneralSKU(**g) for g in general_data["general_skus"]]

    tax_data = ConfigLoader.load_json("tax_rates.json")
    tax_rates = {k: TaxRate(**v) for k, v in tax_data.items()}

    stores = ConfigLoader.list_stores()

    layouts = {}
    tax_profiles = {}
    logo_paths = {}
    store_profiles = {}

    for store in stores:
        store_profiles[store] = StoreProfileConfig(**ConfigLoader.load_store_config(store, "profile.json"))
        layouts[store] = StoreLayoutConfig(**ConfigLoader.load_store_config(store, "layout.json"))
        tax_profiles[store] = ConfigLoader.load_store_config(store, "tax_profile.json")
        logo_paths[store] = str(get_store_logo_path(store))

    return target_skus, general_skus, tax_rates, layouts, tax_profiles, logo_paths, store_profiles

import subprocess

def main():
    # Only run setup generator dynamically if running in development mode (not PyInstaller frozen)
    if not getattr(sys, 'frozen', False):
        if not (get_config_dir() / "target_skus.json").exists():
            subprocess.run([sys.executable, str(project_root / "refactor_configs.py")], check=True)

    target_skus, general_skus, tax_rates, layouts, tax_profiles, logo_paths, store_profiles = load_configs_main()

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
    batch_dir = str(get_next_batch_dir())

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

        # Pick address
        from models.core import StoreAddress
        prof = store_profiles.get(cart.store_id)
        addrs = prof.addresses.get(cart.state_code, [])
        address = StoreAddress(**random.choice(addrs)) if addrs else StoreAddress(store_number="000", street="TEST", city="TEST", state="XX", zip="000")

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
            timestamp=ts_str,
            address=address
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
