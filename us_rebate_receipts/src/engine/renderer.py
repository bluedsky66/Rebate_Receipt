import os
from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal
from models.core import ReceiptData, StoreLayoutConfig

class LayoutRenderer:
    def __init__(self, layouts: dict, logo_paths: dict):
        self.layouts = layouts
        self.logo_paths = logo_paths

        # Load font
        try:
            self.font = ImageFont.truetype("DejaVuSansMono.ttf", 20)
        except:
            self.font = ImageFont.load_default()

    def render_png(self, receipt: ReceiptData) -> Image.Image:
        layout: StoreLayoutConfig = self.layouts.get(receipt.cart.store_id)
        if not layout:
            raise ValueError(f"No layout for store {receipt.cart.store_id}")

        page_width = layout.page_width_dots
        line_height = layout.line_height

        # Determine total height
        num_lines = 10 + len(receipt.cart.items) + 5 + 3 + 4 # approx lines
        height = num_lines * line_height + 200 # + logo height

        img = Image.new('RGB', (page_width, height), color=(255, 255, 255))
        d = ImageDraw.Draw(img)

        y = 10

        # 1. Logo
        logo_path = self.logo_paths.get(receipt.cart.store_id)
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path).convert('L')
            # Floyd-Steinberg dither to 1-bit
            logo = logo.convert('1')

            # Scale if needed
            if logo.width > page_width:
                ratio = page_width / float(logo.width)
                logo = logo.resize((page_width, int(logo.height * ratio)), Image.NEAREST)

            img.paste(logo, ((page_width - logo.width) // 2, y))
            y += logo.height + 20

        # 2. Header
        if layout.header.show_name:
            store_display = receipt.cart.store_id.upper()
            if store_display == "SAMS_CLUB": store_display = "SAM'S CLUB"
            self._draw_text(d, store_display.replace("_", " "), page_width, y, align=layout.header.alignment)
            y += line_height

        if layout.header.show_address:
            addr = receipt.address
            address_str = layout.header.address_template.format(
                store_number=addr.store_number,
                street=addr.street,
                city=addr.city,
                state=addr.state,
                zip=addr.zip
            )
            for line in address_str.split('\n'):
                self._draw_text(d, line, page_width, y, align=layout.header.alignment)
                y += line_height

        y += line_height

        # 3. Items
        for item in receipt.cart.items:
            # Format tax indicator
            indicator = layout.item_line.tax_indicator_taxable if item.is_taxable else layout.item_line.tax_indicator_exempt
            line_tot = str(item.line_total)
            if indicator:
                line_tot += f" {indicator}"

            if layout.item_line.display_mode == "compact":
                # Name and total on same line, qty skipped if 1
                name_str = item.sku.name.upper()[:26]
                if item.qty > 1:
                    qty_str = f"{item.qty} @ {item.unit_price}"
                    self._draw_text(d, name_str, page_width, y, align=layout.item_line.name_align)
                    y += line_height
                    self._draw_text(d, qty_str, page_width, y, align=layout.item_line.name_align)
                else:
                    self._draw_text(d, name_str, page_width, y, align=layout.item_line.name_align)

                self._draw_text(d, line_tot, page_width, y, align=layout.item_line.price_align)
                y += line_height

            else: # detailed
                # Name
                self._draw_text(d, item.sku.name, page_width, y, align=layout.item_line.name_align)
                if layout.item_line.show_upc:
                    y += line_height
                    self._draw_text(d, item.sku.upc, page_width, y, align=layout.item_line.name_align)

                y += line_height

                qty_str = layout.item_line.qty_template.format(qty=item.qty, unit_price=item.unit_price)

                self._draw_text(d, qty_str, page_width, y, align=layout.item_line.name_align)
                self._draw_text(d, line_tot, page_width, y, align=layout.item_line.price_align)

                y += line_height

        y += line_height

        # 4. Total Section
        self._draw_text(d, layout.total_section.separator, page_width, y, align="center")
        y += line_height

        self._draw_text(d, layout.total_section.subtotal_label, page_width, y, align="left")
        self._draw_text(d, str(receipt.cart.subtotal), page_width, y, align="right")
        y += line_height

        # Taxes
        if layout.tax_line_format.mode == "single":
            tax_label = layout.tax_line_format.single_label
            if layout.tax_line_format.show_rate:
                tax_label += " (VARIES%)"
            self._draw_text(d, tax_label, page_width, y, align="left")
            self._draw_text(d, str(receipt.cart.tax_total), page_width, y, align="right")
            y += line_height
        else: # split
            self._draw_text(d, layout.tax_line_format.split_labels[0], page_width, y, align="left")
            self._draw_text(d, str((receipt.cart.tax_total / 2).quantize(Decimal("0.01"))), page_width, y, align="right")
            y += line_height
            self._draw_text(d, layout.tax_line_format.split_labels[1], page_width, y, align="left")
            self._draw_text(d, str((receipt.cart.tax_total / 2).quantize(Decimal("0.01"))), page_width, y, align="right")
            y += line_height

        # Total
        self._draw_text(d, layout.total_section.total_label, page_width, y, align="left")
        self._draw_text(d, str(receipt.cart.total), page_width, y, align="right")
        y += line_height * 2

        # 5. Payment
        pay_label = layout.payment_line.label
        if receipt.payment.type == "CASH":
            pay_str = layout.payment_line.cash_label
            self._draw_text(d, pay_label, page_width, y, align="left")
            self._draw_text(d, pay_str, page_width, y, align="right")
            y += line_height
            for footer_line in layout.payment_line.payment_footer_lines:
                if "CHANGE" in footer_line.upper():
                    line = footer_line.format(change="0.00")
                    self._draw_text(d, line.split("{")[0].strip(), page_width, y, align="left") # Rough formatting
                    self._draw_text(d, "0.00", page_width, y, align="right")
                    y += line_height
        else:
            pay_str = layout.payment_line.mask_format.format(type=receipt.payment.type, last4=receipt.payment.last4)
            self._draw_text(d, pay_label, page_width, y, align="left")
            self._draw_text(d, pay_str, page_width, y, align="right")
            y += line_height
            for footer_line in layout.payment_line.payment_footer_lines:
                if "APPROVED" in footer_line.upper() or "AUTH" in footer_line.upper():
                    self._draw_text(d, footer_line, page_width, y, align="center")
                    y += line_height

        y += line_height * 2

        # 6. Footer
        term_str = layout.footer.terminal_id_format.format(register=receipt.register_id)
        self._draw_text(d, term_str, page_width, y, align="center")
        y += line_height

        txn_str = layout.footer.txn_format.format(
            store_number=receipt.address.store_number,
            store_id=receipt.cart.store_id,
            register=receipt.register_id,
            seq=receipt.txn_seq,
            timestamp=receipt.timestamp
        )
        for line in txn_str.split('\n'):
            self._draw_text(d, line, page_width, y, align="center")
            y += line_height

        # Crop to actual height
        img = img.crop((0, 0, page_width, y + 20))
        return img

    def _draw_text(self, d, text, page_width, y, align="left"):
        bbox = d.textbbox((0, 0), text, font=self.font)
        w = bbox[2] - bbox[0]
        if align == "left":
            x = 10
        elif align == "right":
            x = page_width - w - 10
        else: # center
            x = (page_width - w) // 2

        d.text((x, y), text, font=self.font, fill=(0, 0, 0))

    def render_escpos(self, receipt: ReceiptData) -> bytes:
        layout: StoreLayoutConfig = self.layouts.get(receipt.cart.store_id)
        if not layout:
            raise ValueError(f"No layout for store {receipt.cart.store_id}")

        out = bytearray()

        # 1. Init
        for cmd in layout.custom_escpos:
            out.extend(cmd.encode('latin1'))

        out.extend(b'\x1b\x61\x01') # Center

        # Logo via GS v 0 raster bit image
        logo_path = self.logo_paths.get(receipt.cart.store_id)
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path).convert('1')

            # Ensure width is multiple of 8
            width = logo.width
            if width % 8 != 0:
                width = width + (8 - (width % 8))

            if width > layout.page_width_dots:
                width = layout.page_width_dots

            logo = logo.resize((width, int(logo.height * (width / logo.width))), Image.NEAREST)

            xL = int((width / 8) % 256)
            xH = int((width / 8) / 256)
            yL = int(logo.height % 256)
            yH = int(logo.height / 256)

            # GS v 0
            out.extend(b'\x1d\x76\x30\x00')
            out.extend(bytes([xL, xH, yL, yH]))

            # Rasterize
            pixels = list(logo.getdata())
            for y in range(logo.height):
                for x in range(0, width, 8):
                    byte_val = 0
                    for bit in range(8):
                        if x + bit < logo.width:
                            pixel = pixels[y * logo.width + x + bit]
                            if pixel == 0: # Black
                                byte_val |= (1 << (7 - bit))
                    out.append(byte_val)

            out.extend(b'\n')

        # 2. Header
        if layout.header.show_name:
            store_display = receipt.cart.store_id.upper()
            if store_display == "SAMS_CLUB": store_display = "SAM'S CLUB"
            out.extend(store_display.replace("_", " ").encode() + b'\n')
        if layout.header.show_address:
            addr = receipt.address
            address_str = layout.header.address_template.format(
                store_number=addr.store_number,
                street=addr.street,
                city=addr.city,
                state=addr.state,
                zip=addr.zip
            )
            out.extend(address_str.encode() + b'\n')
        out.extend(b'\n')

        # 3. Items
        out.extend(b'\x1b\x61\x00') # Left
        for item in receipt.cart.items:
            indicator = layout.item_line.tax_indicator_taxable if item.is_taxable else layout.item_line.tax_indicator_exempt
            line_tot = str(item.line_total)
            if indicator:
                line_tot += f" {indicator}"

            if layout.item_line.display_mode == "compact":
                name_str = item.sku.name.upper()[:26]
                if item.qty > 1:
                    qty_str = f"{item.qty} @ {item.unit_price}"
                    out.extend(name_str.encode() + b'\n')
                    spaces = 48 - len(qty_str) - len(line_tot)
                    if spaces < 1: spaces = 1
                    out.extend(qty_str.encode() + (b' ' * spaces) + line_tot.encode() + b'\n')
                else:
                    spaces = 48 - len(name_str) - len(line_tot)
                    if spaces < 1: spaces = 1
                    out.extend(name_str.encode() + (b' ' * spaces) + line_tot.encode() + b'\n')
            else:
                out.extend(item.sku.name.encode() + b'\n')
                if layout.item_line.show_upc:
                    out.extend(item.sku.upc.encode() + b'\n')
                qty_str = layout.item_line.qty_template.format(qty=item.qty, unit_price=item.unit_price)

                spaces = 48 - len(qty_str) - len(line_tot)
                if spaces < 1: spaces = 1
                out.extend(qty_str.encode() + (b' ' * spaces) + line_tot.encode() + b'\n')

        out.extend(b'\n')
        out.extend(layout.total_section.separator.encode() + b'\n')

        # 4. Totals
        sub_spaces = 48 - len(layout.total_section.subtotal_label) - len(str(receipt.cart.subtotal))
        out.extend(layout.total_section.subtotal_label.encode() + (b' ' * sub_spaces) + str(receipt.cart.subtotal).encode() + b'\n')

        tax_spaces = 48 - len("TAX") - len(str(receipt.cart.tax_total))
        out.extend(b'TAX' + (b' ' * tax_spaces) + str(receipt.cart.tax_total).encode() + b'\n')

        tot_spaces = 48 - len(layout.total_section.total_label) - len(str(receipt.cart.total))
        out.extend(layout.total_section.total_label.encode() + (b' ' * tot_spaces) + str(receipt.cart.total).encode() + b'\n')
        out.extend(b'\n')

        # 5. Payment
        if receipt.payment.type == "CASH":
            pay_str = layout.payment_line.cash_label
            pay_spaces = 48 - len(layout.payment_line.label) - len(pay_str)
            out.extend(layout.payment_line.label.encode() + (b' ' * pay_spaces) + pay_str.encode() + b'\n')

            for footer_line in layout.payment_line.payment_footer_lines:
                if "CHANGE" in footer_line.upper():
                    line = footer_line.format(change="0.00")
                    lbl = line.split("{")[0].strip()
                    sps = 48 - len(lbl) - 4
                    out.extend(lbl.encode() + (b' ' * sps) + b'0.00\n')
        else:
            pay_str = layout.payment_line.mask_format.format(type=receipt.payment.type, last4=receipt.payment.last4)
            pay_spaces = 48 - len(layout.payment_line.label) - len(pay_str)
            out.extend(layout.payment_line.label.encode() + (b' ' * pay_spaces) + pay_str.encode() + b'\n')

            for footer_line in layout.payment_line.payment_footer_lines:
                if "APPROVED" in footer_line.upper() or "AUTH" in footer_line.upper():
                    out.extend(b'\x1b\x61\x01') # Center
                    out.extend(footer_line.encode() + b'\n')
                    out.extend(b'\x1b\x61\x00') # Left

        out.extend(b'\n')

        # 6. Footer
        out.extend(b'\x1b\x61\x01') # Center
        term_str = layout.footer.terminal_id_format.format(register=receipt.register_id)
        out.extend(term_str.encode() + b'\n')
        txn_str = layout.footer.txn_format.format(
            store_number=receipt.address.store_number,
            store_id=receipt.cart.store_id,
            register=receipt.register_id,
            seq=receipt.txn_seq,
            timestamp=receipt.timestamp
        )
        out.extend(txn_str.encode() + b'\n')

        # Cut paper
        out.extend(b'\x1d\x56\x41\x00')
        return bytes(out)
