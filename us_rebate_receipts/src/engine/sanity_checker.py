from typing import List
from decimal import Decimal
from us_rebate_receipts.src.models.core import ShoppingCart, PaymentDetail

class PreRenderSanityCheck:
    @staticmethod
    def verify(cart: ShoppingCart, payment: PaymentDetail, affinity_enforce: bool):
        # 1. Decimal exact math
        if cart.subtotal + cart.tax_total != cart.total:
            raise ValueError(f"金额守恒失败：小计 {cart.subtotal} + 税额 {cart.tax_total} != 合计 {cart.total}")

        # 2. Tax precision
        if cart.tax_total.as_tuple().exponent < -2:
            raise ValueError(f"税务精度错误: {cart.tax_total} 的小数位数超过2位")

        # 3. Affinity verification
        if affinity_enforce and cart.scene_anchor_tags:
            for item in cart.items:
                if not set(item.sku.affinity_tags) & cart.scene_anchor_tags:
                    raise ValueError(f"场景亲和度冲突：{item.sku.name} ({item.sku.affinity_tags}) 与目标商品无共同标签")

        # 4. Cash rules
        if cart.total >= Decimal("50.00") and payment.type == "CASH":
            raise ValueError("支付规则冲突：总金额 >= $50 不得使用现金")

        # 5. Costco rules
        if cart.store_id.startswith("costco") and payment.type != "VISA":
            raise ValueError("Costco 门店必须使用 VISA 支付")

        return True
