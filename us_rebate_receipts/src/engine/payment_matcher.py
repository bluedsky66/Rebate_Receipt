import random
from decimal import Decimal
from models.core import RebateJobConfig, ShoppingCart, PaymentDetail

class PaymentMatcher:
    def __init__(self, layouts: dict):
        self.layouts = layouts

    def generate_payment(self, config: RebateJobConfig, cart: ShoppingCart) -> PaymentDetail:
        store_id = cart.store_id
        amount = cart.total
        mode = config.payment_mode

        # Costco rule
        if store_id.startswith("costco"):
            return PaymentDetail(
                type="VISA",
                amount=amount,
                last4=f"{random.randint(1000, 9999)}"
            )

        layout = self.layouts.get(store_id)
        if not layout:
            raise ValueError(f"No layout found for store {store_id}")

        walmart_pay = layout.payment_line.store_specific.walmart_pay
        wp_threshold = Decimal(layout.payment_line.store_specific.walmart_pay_threshold or "100.00")

        target_redcard = store_id == "target"

        if mode == "auto":
            if walmart_pay and amount > wp_threshold and random.random() < 0.40:
                type_ = "WALMART PAY"
            elif target_redcard and random.random() < 0.35:
                type_ = "REDCARD"
            elif amount >= Decimal("50.00"):
                type_ = random.choice(["VISA", "MC", "AMEX", "DISCOVER"])
            elif amount < Decimal("20.00"):
                if random.random() < 0.70:
                    type_ = "CASH"
                else:
                    type_ = random.choice(["VISA", "MC", "AMEX", "DISCOVER"])
            else:
                if random.random() < 0.15:
                    type_ = "CASH"
                else:
                    type_ = random.choice(["VISA", "MC", "AMEX", "DISCOVER"])
        elif mode == "cash":
            type_ = "CASH"
        elif mode == "card":
            if target_redcard and random.random() < 0.35:
                type_ = "REDCARD"
            else:
                type_ = random.choice(["VISA", "MC", "AMEX", "DISCOVER"])
        else:
             type_ = "CASH"

        last4 = f"{random.randint(1000, 9999)}" if type_ != "CASH" else None

        return PaymentDetail(
            type=type_, # type: ignore
            amount=amount,
            last4=last4
        )
