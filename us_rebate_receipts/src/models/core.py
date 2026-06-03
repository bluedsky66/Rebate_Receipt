import json
from decimal import Decimal
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SKUBase(BaseModel):
    sku_id: str
    upc: str
    name: str
    base_price: Decimal
    category: str
    affinity_tags: List[str]

    @field_validator("base_price", mode="before")
    @classmethod
    def parse_price(cls, v):
        if isinstance(v, str):
            return Decimal(v)
        return v

class TargetSKU(SKUBase):
    rebate_price: Decimal
    min_qty: int = 1
    valid_stores: List[str]
    valid_states: List[str]
    weight: int = 100

    @field_validator("rebate_price", mode="before")
    @classmethod
    def parse_rebate_price(cls, v):
        if isinstance(v, str):
            return Decimal(v)
        return v

class GeneralSKU(SKUBase):
    weight: int

class TaxRate(BaseModel):
    state_code: str
    state_rate: Decimal
    local_avg: Decimal
    food_exempt: bool = False
    split_tax: bool = False

    @field_validator("state_rate", "local_avg", mode="before")
    @classmethod
    def parse_rates(cls, v):
        if isinstance(v, str):
            return Decimal(v)
        return v

class RebateJobConfig(BaseModel):
    # Target Items
    target_skus: List[str]
    target_qty_mode: Literal["fixed", "range"] = "fixed"
    target_qty_value: int | Tuple[int, int] = 1

    # Filler Items
    filler_strategy: Literal["smart", "random", "none"] = "smart"
    filler_count_range: Tuple[int, int] = (3, 8)
    affinity_enforce: bool = True

    # Store & State
    store_filter: Optional[List[str]] = None
    state_filter: Optional[List[str]] = None

    # Registers
    register_pool: List[str] = Field(default_factory=lambda: ["01", "02", "03", "04", "05"])
    register_mode: Literal["random", "round_robin", "fixed"] = "random"
    void_ratio: float = 0.05
    return_ratio: float = 0.02

    # Payment
    payment_mode: Literal["auto", "cash", "card"] = "auto"

    # Output
    output_format: Literal["png", "direct_print"] = "png"
    count: int = 1

    # Time settings
    time_mode: Literal["recent", "fixed", "range"] = "recent"
    time_fixed: Optional[str] = None # ISO format
    time_range_start: Optional[str] = None # ISO format
    time_range_end: Optional[str] = None # ISO format

class CartItem(BaseModel):
    sku: SKUBase
    qty: int
    unit_price: Decimal
    line_total: Decimal
    is_target: bool
    is_taxable: bool = True

class ShoppingCart(BaseModel):
    store_id: str
    state_code: str
    items: List[CartItem]
    subtotal: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    scene_anchor_tags: set[str] = Field(default_factory=set)

class PaymentDetail(BaseModel):
    type: Literal["CASH", "VISA", "MC", "AMEX", "DISCOVER", "WALMART PAY", "REDCARD"]
    amount: Decimal
    last4: Optional[str] = None

class StoreAddress(BaseModel):
    store_number: str
    street: str
    city: str
    state: str
    zip: str

class StoreProfileConfig(BaseModel):
    store_id: str
    name: str
    region_whitelist: List[str]
    addresses: dict # state -> List[StoreAddress]
    layout_id: str
    logo_path: str
    tax_profile_id: str
    register_pool: List[str]
    register_mode: str
    store_type: str

class ReceiptData(BaseModel):
    job_id: str
    cart: ShoppingCart
    payment: PaymentDetail
    register_id: str
    txn_seq: int
    timestamp: str # ISO 8601 or similar formatted time string
    address: StoreAddress

class HeaderConfig(BaseModel):
    alignment: str
    show_name: bool
    show_address: bool
    address_template: str

class ItemLineConfig(BaseModel):
    display_mode: Literal["detailed", "compact"] = "detailed"
    name_align: str
    price_align: str
    price_offset: int
    qty_template: str
    show_upc: bool
    tax_indicator_taxable: str = "T"
    tax_indicator_exempt: str = ""

class TaxLineFormat(BaseModel):
    mode: str
    single_label: str
    split_labels: List[str]
    show_rate: bool
    alignment: str
    separator: str

class PaymentStoreSpecific(BaseModel):
    walmart_pay: bool = False
    walmart_pay_threshold: Optional[str] = None
    costco_visa_only: bool = False

class PaymentLineConfig(BaseModel):
    label: str
    alignment: str
    mask_format: str
    cash_label: str
    store_specific: PaymentStoreSpecific
    payment_footer_lines: List[str] = Field(default_factory=list)

class TotalSectionConfig(BaseModel):
    subtotal_label: str
    tax_label: str
    total_label: str
    separator: str

class FooterConfig(BaseModel):
    barcode_type: str
    terminal_id_format: str
    txn_format: str
    show_time: bool
    time_format: str

class StoreLayoutConfig(BaseModel):
    store_id: str
    page_width_dots: int
    line_height: int
    char_spacing: int
    header: HeaderConfig
    item_line: ItemLineConfig
    tax_line_format: TaxLineFormat
    payment_line: PaymentLineConfig
    total_section: TotalSectionConfig
    footer: FooterConfig
    custom_escpos: List[str]
