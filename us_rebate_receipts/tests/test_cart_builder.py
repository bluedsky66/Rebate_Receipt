import pytest
from decimal import Decimal
from us_rebate_receipts.src.models.core import TargetSKU, GeneralSKU, RebateJobConfig
from us_rebate_receipts.src.engine.cart_builder import CartBuilder

@pytest.fixture
def test_skus():
    targets = [
        TargetSKU(
            sku_id="T1", upc="111", name="Tide", base_price="12.99", rebate_price="12.99",
            valid_stores=["walmart"], valid_states=["CA"], category="Household",
            affinity_tags=["laundry"], weight=100
        )
    ]
    generals = [
        GeneralSKU(
            sku_id="G1", upc="222", name="Downy", base_price="5.99",
            category="Household", affinity_tags=["laundry", "fabric_care"], weight=100
        ),
        GeneralSKU(
            sku_id="G1_2", upc="222_2", name="Downy 2", base_price="5.99",
            category="Household", affinity_tags=["laundry", "fabric_care"], weight=100
        ),
        GeneralSKU(
            sku_id="G2", upc="333", name="Diamond Ring", base_price="999.99",
            category="Jewelry", affinity_tags=["jewelry"], weight=100
        )
    ]
    return targets, generals

def test_cart_builder_affinity_pass(test_skus):
    targets, generals = test_skus
    builder = CartBuilder(targets, generals)

    config = RebateJobConfig(
        target_skus=["T1"], filler_strategy="smart", filler_count_range=(2, 2), affinity_enforce=True,
        output_format="png", count=1
    )

    cart = builder.build_cart(config)
    assert len(cart.items) == 3
    assert "laundry" in cart.scene_anchor_tags
    names = [i.sku.name for i in cart.items]
    assert "Tide" in names
    assert "Downy" in names

def test_cart_builder_affinity_reject(test_skus):
    targets, generals = test_skus
    # Remove Downy so only Diamond Ring is left as general
    builder = CartBuilder(targets, [generals[1]])

    config = RebateJobConfig(
        target_skus=["T1"], filler_strategy="smart", filler_count_range=(2, 2), affinity_enforce=True,
        output_format="png", count=1
    )

    with pytest.raises(ValueError, match="场景池商品不足"):
        builder.build_cart(config)
