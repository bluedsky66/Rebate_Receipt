import json
import random
from typing import List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

from us_rebate_receipts.src.models.core import (
    TargetSKU, GeneralSKU, RebateJobConfig, CartItem, ShoppingCart,
    TaxRate, StoreLayoutConfig, PaymentDetail
)

class CartBuilder:
    def __init__(self, target_skus: List[TargetSKU], general_skus: List[GeneralSKU]):
        self.target_skus = {sku.sku_id: sku for sku in target_skus}
        self.general_skus = general_skus

    def build_cart(self, config: RebateJobConfig) -> ShoppingCart:
        # Determine valid stores and states from targets
        targets = [self.target_skus[sku_id] for sku_id in config.target_skus]

        valid_stores = set(targets[0].valid_stores)
        valid_states = set(targets[0].valid_states)
        scene_anchor_tags = set(targets[0].affinity_tags)

        for target in targets[1:]:
            valid_stores &= set(target.valid_stores)
            valid_states &= set(target.valid_states)
            scene_anchor_tags |= set(target.affinity_tags)

        if config.store_filter:
            valid_stores &= set(config.store_filter)
        if config.state_filter:
            valid_states &= set(config.state_filter)

        if not valid_stores:
            raise ValueError("Pre-validation failed: No common valid stores for target SKUs")
        if not valid_states:
            raise ValueError("Pre-validation failed: No common valid states for target SKUs")

        store_id = random.choice(list(valid_stores))
        state_code = random.choice(list(valid_states))

        cart_items = []
        for target in targets:
            qty = target.min_qty
            if config.target_qty_mode == "fixed":
                qty = max(qty, int(config.target_qty_value))
            else:
                min_v, max_v = config.target_qty_value
                qty = max(qty, random.randint(min_v, max_v))

            # Rebate price float +/- 5% max $0.30
            float_amt = min(target.rebate_price * Decimal("0.05"), Decimal("0.30"))
            cents = int(float_amt * 100)
            if cents > 0:
                float_adj = Decimal(random.randint(-cents, cents)) / Decimal(100)
            else:
                float_adj = Decimal("0.00")

            unit_price = target.rebate_price + float_adj
            unit_price = unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            line_total = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            cart_items.append(CartItem(
                sku=target,
                qty=qty,
                unit_price=unit_price,
                line_total=line_total,
                is_target=True,
                is_taxable=True # Overridden by TaxEngine later if needed
            ))

        # Fillers
        if config.filler_strategy != "none":
            count = random.randint(config.filler_count_range[0], config.filler_count_range[1])

            scene_pool = []
            if config.filler_strategy == "smart" or config.affinity_enforce:
                 scene_pool = [
                    sku for sku in self.general_skus
                    if set(sku.affinity_tags) & scene_anchor_tags
                 ]
            else:
                scene_pool = self.general_skus

            if config.affinity_enforce and len(scene_pool) == 0:
                raise ValueError("Scene pool empty: Insufficient general SKUs sharing affinity tags with targets.")

            # If not enough, pick what we can
            scene_pool = scene_pool or self.general_skus

            weights = [sku.weight for sku in scene_pool]
            try:
                chosen_fillers = random.choices(scene_pool, weights=weights, k=count)
            except Exception:
                chosen_fillers = []

            for filler in chosen_fillers:
                qty = 1
                unit_price = filler.base_price
                line_total = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                cart_items.append(CartItem(
                    sku=filler,
                    qty=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                    is_target=False,
                    is_taxable=True
                ))

        # We shuffle so targets aren't always at the top
        random.shuffle(cart_items)

        return ShoppingCart(
            store_id=store_id,
            state_code=state_code,
            items=cart_items,
            scene_anchor_tags=scene_anchor_tags
        )
