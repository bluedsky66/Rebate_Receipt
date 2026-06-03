import pytest
from decimal import Decimal
from us_rebate_receipts.src.models.core import ShoppingCart, PaymentDetail, CartItem, GeneralSKU
from us_rebate_receipts.src.engine.sanity_checker import PreRenderSanityCheck

def create_item(name, price, tags):
    sku = GeneralSKU(sku_id="1", upc="1", name=name, base_price=price, category="X", affinity_tags=tags, weight=1)
    return CartItem(sku=sku, qty=1, unit_price=Decimal(price), line_total=Decimal(price), is_target=False)

def test_decimal_conservation():
    cart = ShoppingCart(
        store_id="walmart", state_code="CA", items=[],
        subtotal=Decimal("10.00"), tax_total=Decimal("1.00"), total=Decimal("11.01")
    )
    payment = PaymentDetail(type="VISA", amount=Decimal("11.01"))

    with pytest.raises(ValueError, match="Math violation"):
        PreRenderSanityCheck.verify(cart, payment, False)

def test_affinity_violation():
    cart = ShoppingCart(
        store_id="walmart", state_code="CA",
        items=[create_item("Ring", "100.00", ["jewelry"])],
        scene_anchor_tags={"laundry"},
        subtotal=Decimal("100.00"), tax_total=Decimal("0.00"), total=Decimal("100.00")
    )
    payment = PaymentDetail(type="VISA", amount=Decimal("100.00"))

    with pytest.raises(ValueError, match="Affinity violation"):
        PreRenderSanityCheck.verify(cart, payment, True)

def test_cash_rule_violation():
    cart = ShoppingCart(
        store_id="walmart", state_code="CA", items=[],
        subtotal=Decimal("60.00"), tax_total=Decimal("0.00"), total=Decimal("60.00")
    )
    payment = PaymentDetail(type="CASH", amount=Decimal("60.00"))

    with pytest.raises(ValueError, match="Cash payment for amount"):
        PreRenderSanityCheck.verify(cart, payment, False)

def test_costco_visa_violation():
    cart = ShoppingCart(
        store_id="costco", state_code="CA", items=[],
        subtotal=Decimal("60.00"), tax_total=Decimal("0.00"), total=Decimal("60.00")
    )
    payment = PaymentDetail(type="MC", amount=Decimal("60.00"))

    with pytest.raises(ValueError, match="Costco requires VISA"):
        PreRenderSanityCheck.verify(cart, payment, False)
