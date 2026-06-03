from decimal import Decimal, ROUND_HALF_UP
from us_rebate_receipts.src.models.core import ShoppingCart

class TaxEngine:
    def __init__(self, tax_rates: dict, store_tax_profiles: dict):
        self.tax_rates = tax_rates # dict of state_code -> TaxRate
        self.store_profiles = store_tax_profiles # dict of store_id -> tax_profile dict

    def calculate_taxes(self, cart: ShoppingCart) -> ShoppingCart:
        tax_rate = self.tax_rates.get(cart.state_code)
        if not tax_rate:
            raise ValueError(f"Tax rate not found for state {cart.state_code}")

        store_profile = self.store_profiles.get(cart.store_id, {})
        mixed_rates = store_profile.get("mixed_rates", False)

        # Exempt categories roughly
        food_categories = {"Produce", "Dairy", "Baby Food", "Groceries", "Snacks", "Beverages"}

        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")

        for item in cart.items:
            subtotal += item.line_total

            # Determine if taxable
            is_taxable = True
            if tax_rate.food_exempt and item.sku.category in food_categories:
                is_taxable = False

            item.is_taxable = is_taxable

            if is_taxable:
                combined_rate = tax_rate.state_rate + tax_rate.local_avg
                item_tax = (item.line_total * combined_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_total += item_tax

        cart.subtotal = subtotal
        cart.tax_total = tax_total
        cart.total = subtotal + tax_total

        return cart
