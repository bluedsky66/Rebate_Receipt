import sys
import json
import random
import hashlib
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QAbstractItemView,
    QMessageBox, QSplitter, QScrollArea, QGroupBox, QFormLayout,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QLineEdit
)
from PyQt6.QtGui import QPixmap, QImage, QAction
from PyQt6.QtCore import Qt

from us_rebate_receipts.src.models.core import RebateJobConfig
from us_rebate_receipts.main import load_configs
from us_rebate_receipts.src.engine.cart_builder import CartBuilder
from us_rebate_receipts.src.engine.tax_engine import TaxEngine
from us_rebate_receipts.src.engine.payment_matcher import PaymentMatcher
from us_rebate_receipts.src.engine.txn_lock import RegisterAwareTxnLock
from us_rebate_receipts.src.engine.sanity_checker import PreRenderSanityCheck
from us_rebate_receipts.src.engine.renderer import LayoutRenderer
from us_rebate_receipts.src.printers.printers import PngPrinter, DirectPrinter

class PreviewDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt Preview")
        self.setMinimumSize(450, 600)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(lbl)

        layout.addWidget(scroll)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("US Rebate Receipt Generator")
        self.setMinimumSize(1000, 700)

        self.txn_lock = RegisterAwareTxnLock()

        self.create_menu()
        self.load_data()
        self.init_ui()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        config_menu = menubar.addMenu("Config")
        reload_act = QAction("Reload JSONs", self)
        reload_act.triggered.connect(self.reload_data)
        config_menu.addAction(reload_act)

    def load_data(self):
        try:
            self.target_skus, self.general_skus, self.tax_rates, self.layouts, self.tax_profiles, self.logo_paths = load_configs()
            self.cart_builder = CartBuilder(self.target_skus, self.general_skus)
            self.tax_engine = TaxEngine(self.tax_rates, self.tax_profiles)
            self.payment_matcher = PaymentMatcher(self.layouts)
            self.renderer = LayoutRenderer(self.layouts, self.logo_paths)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def reload_data(self):
        self.load_data()
        self.populate_lists()
        QMessageBox.information(self, "Success", "Configurations reloaded.")

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left Panel - Config
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        config_widget = QWidget()
        form = QFormLayout(config_widget)

        # Targets
        self.lst_targets = QListWidget()
        self.lst_targets.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_targets.setMinimumHeight(100)
        form.addRow("Target SKUs:", self.lst_targets)

        self.cb_qty_mode = QComboBox()
        self.cb_qty_mode.addItems(["fixed", "range"])
        form.addRow("Target Qty Mode:", self.cb_qty_mode)

        self.sp_qty = QSpinBox()
        self.sp_qty.setRange(1, 100)
        form.addRow("Target Qty (Fixed/Max):", self.sp_qty)

        # Fillers
        self.cb_filler_strategy = QComboBox()
        self.cb_filler_strategy.addItems(["smart", "random", "none"])
        form.addRow("Filler Strategy:", self.cb_filler_strategy)

        self.sp_filler_min = QSpinBox()
        self.sp_filler_max = QSpinBox()
        self.sp_filler_max.setValue(5)

        filler_layout = QHBoxLayout()
        filler_layout.addWidget(self.sp_filler_min)
        filler_layout.addWidget(QLabel("-"))
        filler_layout.addWidget(self.sp_filler_max)
        form.addRow("Filler Count Range:", filler_layout)

        self.chk_affinity = QCheckBox("Enforce Affinity Tags")
        self.chk_affinity.setChecked(True)
        form.addRow("", self.chk_affinity)

        # Store & State
        self.lst_stores = QListWidget()
        self.lst_stores.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_stores.setMinimumHeight(80)
        form.addRow("Store Filter:", self.lst_stores)

        self.lst_states = QListWidget()
        self.lst_states.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_states.setMinimumHeight(80)
        form.addRow("State Filter:", self.lst_states)

        # Registers
        self.le_registers = QLineEdit("01,02,03,04,05")
        form.addRow("Register Pool:", self.le_registers)

        self.cb_reg_mode = QComboBox()
        self.cb_reg_mode.addItems(["random", "round_robin", "fixed"])
        form.addRow("Register Mode:", self.cb_reg_mode)

        self.sp_void = QDoubleSpinBox()
        self.sp_void.setRange(0.0, 0.3)
        self.sp_void.setSingleStep(0.01)
        self.sp_void.setValue(0.05)
        form.addRow("Void Ratio:", self.sp_void)

        self.sp_return = QDoubleSpinBox()
        self.sp_return.setRange(0.0, 0.3)
        self.sp_return.setSingleStep(0.01)
        self.sp_return.setValue(0.02)
        form.addRow("Return Ratio:", self.sp_return)

        # Payment
        self.cb_payment = QComboBox()
        self.cb_payment.addItems(["auto", "cash", "card"])
        form.addRow("Payment Mode:", self.cb_payment)

        # Output
        self.cb_output = QComboBox()
        self.cb_output.addItems(["png", "direct_print"])
        form.addRow("Output Format:", self.cb_output)

        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, 1000)
        form.addRow("Batch Count:", self.sp_count)

        # Actions
        btn_layout = QHBoxLayout()
        self.btn_validate = QPushButton("Validate Config")
        self.btn_preview = QPushButton("Preview")
        self.btn_batch = QPushButton("Batch Generate")

        btn_layout.addWidget(self.btn_validate)
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_batch)
        form.addRow(btn_layout)

        self.btn_validate.clicked.connect(self.validate_config)
        self.btn_preview.clicked.connect(self.do_preview)
        self.btn_batch.clicked.connect(self.do_batch)

        scroll.setWidget(config_widget)
        left_layout.addWidget(scroll)

        # Right Panel - Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.lbl_preview = QLabel("Preview will appear here.")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll_preview = QScrollArea()
        scroll_preview.setWidgetResizable(True)
        scroll_preview.setWidget(self.lbl_preview)

        right_layout.addWidget(scroll_preview)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        self.populate_lists()

    def populate_lists(self):
        self.lst_targets.clear()
        for t in self.target_skus:
            item = QListWidgetItem(f"{t.name} (${t.rebate_price})")
            item.setData(Qt.ItemDataRole.UserRole, t.sku_id)
            self.lst_targets.addItem(item)

        self.lst_stores.clear()
        self.lst_stores.addItem(QListWidgetItem("All"))
        for s in self.layouts.keys():
            self.lst_stores.addItem(s)

        self.lst_states.clear()
        self.lst_states.addItem(QListWidgetItem("All"))
        for st in self.tax_rates.keys():
            self.lst_states.addItem(st)

    def get_config(self) -> RebateJobConfig:
        targets = [i.data(Qt.ItemDataRole.UserRole) for i in self.lst_targets.selectedItems()]
        if not targets:
            raise ValueError("Select at least one target SKU.")

        stores = [i.text() for i in self.lst_stores.selectedItems()]
        if not stores or "All" in stores:
            stores = None

        states = [i.text() for i in self.lst_states.selectedItems()]
        if not states or "All" in states:
            states = None

        regs = [r.strip() for r in self.le_registers.text().split(",") if r.strip()]

        return RebateJobConfig(
            target_skus=targets,
            target_qty_mode=self.cb_qty_mode.currentText(),
            target_qty_value=self.sp_qty.value() if self.cb_qty_mode.currentText() == "fixed" else (1, self.sp_qty.value()),
            filler_strategy=self.cb_filler_strategy.currentText(),
            filler_count_range=(self.sp_filler_min.value(), self.sp_filler_max.value()),
            affinity_enforce=self.chk_affinity.isChecked(),
            store_filter=stores,
            state_filter=states,
            register_pool=regs,
            register_mode=self.cb_reg_mode.currentText(),
            void_ratio=self.sp_void.value(),
            return_ratio=self.sp_return.value(),
            payment_mode=self.cb_payment.currentText(),
            output_format=self.cb_output.currentText(),
            count=self.sp_count.value()
        )

    def validate_config(self):
        try:
            cfg = self.get_config()
            QMessageBox.information(self, "Valid", "Configuration is valid!")
        except Exception as e:
            QMessageBox.warning(self, "Invalid Configuration", str(e))

    def generate_single(self, config: RebateJobConfig, job_id: str):
        cart = self.cart_builder.build_cart(config)
        cart = self.tax_engine.calculate_taxes(cart)
        payment = self.payment_matcher.generate_payment(config, cart)

        register_id = random.choice(config.register_pool)
        if random.random() < config.void_ratio:
            self.txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "VOID", job_id)
        if random.random() < config.return_ratio:
            self.txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "RETURN", job_id)

        txn_seq, ts = self.txn_lock.next_seq(cart.store_id, register_id, job_id)

        layout = self.layouts[cart.store_id]
        ts_str = datetime.fromtimestamp(ts).strftime(layout.footer.time_format)

        from us_rebate_receipts.src.models.core import ReceiptData
        receipt = ReceiptData(
            job_id=job_id,
            cart=cart,
            payment=payment,
            register_id=register_id,
            txn_seq=txn_seq,
            timestamp=ts_str
        )

        PreRenderSanityCheck.verify(receipt.cart, receipt.payment, config.affinity_enforce)
        return receipt, register_id, txn_seq

    def do_preview(self):
        try:
            config = self.get_config()
            config.output_format = "png" # Force PNG for preview

            job_id = "PREVIEW-001"
            receipt, reg_id, seq = self.generate_single(config, job_id)

            img = self.renderer.render_png(receipt)

            # Convert PIL to QPixmap
            import io
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            qimg = QImage()
            qimg.loadFromData(bio.getvalue())
            pixmap = QPixmap.fromImage(qimg)

            self.lbl_preview.setPixmap(pixmap)

            dlg = PreviewDialog(pixmap, self)
            dlg.exec()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Preview Error", str(e))

    def do_batch(self):
        try:
            config = self.get_config()
            job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            batch_dir = f"us_rebate_receipts/output/{datetime.now().strftime('%Y-%m-%d')}_batch_{job_id[-4:]}"

            png_printer = PngPrinter(batch_dir)
            direct_printer = DirectPrinter(batch_dir)

            success_count = 0
            for i in range(config.count):
                receipt, reg_id, seq = self.generate_single(config, job_id)

                if config.output_format == "png":
                    img = self.renderer.render_png(receipt)
                    filename = f"receipt_{job_id}_{i:03d}.png"
                    path = png_printer.print_receipt(img, filename)
                    with open(path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                else:
                    data = self.renderer.render_escpos(receipt)
                    filename = f"direct_print_debug_{job_id}_{i:03d}.bin"
                    path = direct_printer.print_receipt(data, filename)
                    file_hash = hashlib.sha256(data).hexdigest()

                self.txn_lock.update_transaction(receipt.cart.store_id, reg_id, seq, float(receipt.cart.total), file_hash)
                success_count += 1

            QMessageBox.information(self, "Batch Complete", f"Successfully generated {success_count} receipts to {batch_dir}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Batch Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
