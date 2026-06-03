import pytest
from decimal import Decimal
from models.core import ShoppingCart, RebateJobConfig
from engine.payment_matcher import PaymentMatcher

@pytest.fixture
def layouts():
    return {
        "costco": {},
        "walmart": type("LayoutMock", (object,), {
            "payment_line": type("PaymentLineMock", (object,), {
                "store_specific": type("StoreSpecificMock", (object,), {
                    "walmart_pay": True,
                    "walmart_pay_threshold": "100.00",
                    "costco_visa_only": False
                })()
            })()
        })()
    }

def test_costco_forces_visa(layouts):
    matcher = PaymentMatcher(layouts)
    cart = ShoppingCart(store_id="costco", state_code="CA", items=[], total=Decimal("150.00"))
    config = RebateJobConfig(target_skus=[], payment_mode="auto")

    pay = matcher.generate_payment(config, cart)
    assert pay.type == "VISA"

def test_walmart_pay_threshold(layouts, monkeypatch):
    matcher = PaymentMatcher(layouts)
    cart = ShoppingCart(store_id="walmart", state_code="CA", items=[], total=Decimal("150.00"))
    config = RebateJobConfig(target_skus=[], payment_mode="auto")

    # Force random to trigger walmart pay
    monkeypatch.setattr("random.random", lambda: 0.1)

    pay = matcher.generate_payment(config, cart)
    assert pay.type == "WALMART PAY"
