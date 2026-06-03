from typing import List
from decimal import Decimal
from us_rebate_receipts.src.models.core import ShoppingCart, PaymentDetail

class PreRenderSanityCheck:
    @staticmethod
    def verify(cart: ShoppingCart, payment: PaymentDetail, affinity_enforce: bool):
        # 1. Decimal exact math
        if cart.subtotal + cart.tax_total != cart.total:
            raise ValueError(f"Math violation: {cart.subtotal} + {cart.tax_total} != {cart.total}")

        # 2. Tax precision
        if cart.tax_total.as_tuple().exponent < -2:
            raise ValueError(f"Tax precision violation: {cart.tax_total} has more than 2 decimal places")

        # 3. Affinity verification
        if affinity_enforce and cart.scene_anchor_tags:
            for item in cart.items:
                if not set(item.sku.affinity_tags) & cart.scene_anchor_tags:
                    raise ValueError(f"Affinity violation: {item.sku.name} ({item.sku.affinity_tags}) has no intersection with anchor {cart.scene_anchor_tags}")

        # 4. Cash rules
        if cart.total >= Decimal("50.00") and payment.type == "CASH":
            raise ValueError("Payment violation: Cash payment for amount >= $50.00")

        # 5. Costco rules
        if cart.store_id.startswith("costco") and payment.type != "VISA":
            raise ValueError(f"Payment violation: Costco requires VISA, got {payment.type}")

        return True
