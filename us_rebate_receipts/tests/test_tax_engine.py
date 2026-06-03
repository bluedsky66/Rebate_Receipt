import pytest
from decimal import Decimal
from us_rebate_receipts.src.models.core import ShoppingCart, CartItem, GeneralSKU, TaxRate
from us_rebate_receipts.src.engine.tax_engine import TaxEngine

@pytest.fixture
def tax_rates():
    return {
        "CA": TaxRate(state_code="CA", state_rate="0.0725", local_avg="0.0150", food_exempt=True, split_tax=True),
        "OR": TaxRate(state_code="OR", state_rate="0.0000", local_avg="0.0000", food_exempt=True, split_tax=False),
        "TX": TaxRate(state_code="TX", state_rate="0.0625", local_avg="0.0200", food_exempt=True, split_tax=False)
    }

@pytest.fixture
def profiles():
    return {"walmart": {"mixed_rates": False}}

def create_item(name, price, cat):
    sku = GeneralSKU(sku_id="1", upc="1", name=name, base_price=price, category=cat, affinity_tags=["x"], weight=1)
    return CartItem(sku=sku, qty=1, unit_price=Decimal(price), line_total=Decimal(price), is_target=False)

def test_california_tax(tax_rates, profiles):
    engine = TaxEngine(tax_rates, profiles)
    cart = ShoppingCart(store_id="walmart", state_code="CA", items=[
        create_item("TV", "100.00", "Electronics"),
        create_item("Apple", "5.00", "Produce")
    ])

    cart = engine.calculate_taxes(cart)
    # Food exempt
    assert cart.items[1].is_taxable is False
    assert cart.items[0].is_taxable is True
    # Rate: 0.0725 + 0.0150 = 0.0875. 100 * 0.0875 = 8.75
    assert cart.tax_total == Decimal("8.75")
    assert cart.total == Decimal("113.75")

def test_oregon_zero_tax(tax_rates, profiles):
    engine = TaxEngine(tax_rates, profiles)
    cart = ShoppingCart(store_id="walmart", state_code="OR", items=[
        create_item("TV", "100.00", "Electronics")
    ])
    cart = engine.calculate_taxes(cart)
    assert cart.tax_total == Decimal("0.00")
    assert cart.total == Decimal("100.00")
