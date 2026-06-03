import json
import random
from typing import List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

from models.core import (
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

        # Adjust weight for convenience stores
        store_type = "standard"
        if store_id in ["walgreens", "mendez_fuel", "abc_fine_wine", "crown_wine", "discount_drug_mart", "cvs"]:
            store_type = "convenience"

        # Fillers
        if config.filler_strategy != "none":
            count_min = max(2, config.filler_count_range[0])
            count_max = max(count_min, config.filler_count_range[1])
            count = random.randint(count_min, count_max)

            scene_pool = []
            if config.filler_strategy == "smart" or config.affinity_enforce:
                 scene_pool = [
                    sku for sku in self.general_skus
                    if set(sku.affinity_tags) & scene_anchor_tags
                 ]
            else:
                scene_pool = self.general_skus

            if config.affinity_enforce and len(scene_pool) < count:
                raise ValueError(f"场景池商品不足，请扩展通用商品库或降低凑单数量 (需要 {count} 个，只有 {len(scene_pool)} 个)")

            # If not enough, pick what we can
            scene_pool = scene_pool or self.general_skus

            weights = []
            for sku in scene_pool:
                w = sku.weight
                if store_type == "convenience":
                    # bias towards $2-$8 items
                    if Decimal("2.00") <= sku.base_price <= Decimal("8.00"):
                        w *= 5
                weights.append(w)

            # Random choice without replacement (unique SKUs)
            chosen_fillers = []
            try:
                # Need to use random.choices with replacement manually or just weighted sample
                # Since Python doesn't have a weighted random.sample, we do it manually
                pool_copy = list(scene_pool)
                weights_copy = list(weights)
                for _ in range(min(count, len(pool_copy))):
                    chosen = random.choices(pool_copy, weights=weights_copy, k=1)[0]
                    chosen_fillers.append(chosen)
                    idx = pool_copy.index(chosen)
                    pool_copy.pop(idx)
                    weights_copy.pop(idx)
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
