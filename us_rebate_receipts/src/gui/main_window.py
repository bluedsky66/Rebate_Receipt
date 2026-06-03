import random
import hashlib
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QAbstractItemView,
    QMessageBox, QSplitter, QScrollArea, QGroupBox, QFormLayout,
    QLineEdit, QDateTimeEdit, QStackedWidget
)
from PyQt6.QtGui import QPixmap, QImage, QAction
from PyQt6.QtCore import Qt, QDateTime

from models.core import RebateJobConfig, StoreAddress
from engine.cart_builder import CartBuilder
from engine.tax_engine import TaxEngine
from engine.payment_matcher import PaymentMatcher
from engine.txn_lock import RegisterAwareTxnLock
from engine.sanity_checker import PreRenderSanityCheck
from engine.renderer import LayoutRenderer
from printers.printers import PngPrinter, DirectPrinter
from engine.time_utils import generate_timestamp
from utils.output_helper import get_next_batch_dir
from gui.preview_dialog import PreviewDialog
import utils.config_loader

# Need a local load_configs_gui hook from config_loader logic
def load_configs_gui():
    from utils.config_loader import ConfigLoader
    from models.core import TargetSKU, GeneralSKU, TaxRate, StoreLayoutConfig, StoreProfileConfig
    from utils.path_helper import get_store_logo_path

    target_data = ConfigLoader.load_json("target_skus.json")
    target_skus = [TargetSKU(**t) for t in target_data["target_skus"]]

    general_data = ConfigLoader.load_json("general_skus.json")
    general_skus = [GeneralSKU(**g) for g in general_data["general_skus"]]

    tax_data = ConfigLoader.load_json("tax_rates.json")
    tax_rates = {k: TaxRate(**v) for k, v in tax_data.items()}

    stores = ConfigLoader.list_stores()

    layouts = {}
    tax_profiles = {}
    logo_paths = {}
    store_profiles = {}

    for store in stores:
        store_profiles[store] = StoreProfileConfig(**ConfigLoader.load_store_config(store, "profile.json"))
        layouts[store] = StoreLayoutConfig(**ConfigLoader.load_store_config(store, "layout.json"))
        tax_profiles[store] = ConfigLoader.load_store_config(store, "tax_profile.json")
        logo_paths[store] = str(get_store_logo_path(store))

    return target_skus, general_skus, tax_rates, layouts, tax_profiles, logo_paths, store_profiles

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("US Rebate Receipt Generator")
        self.setMinimumSize(1000, 750)

        self.txn_lock = RegisterAwareTxnLock()

        self.create_menu()
        self.load_data()
        self.init_ui()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")

        exit_act = QAction("退出", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        config_menu = menubar.addMenu("配置")
        reload_act = QAction("重新加载所有配置", self)
        reload_act.triggered.connect(self.reload_data)
        config_menu.addAction(reload_act)

    def load_data(self):
        try:
            import os
            import sys
            from utils.path_helper import get_config_dir
            if not getattr(sys, 'frozen', False):
                if not (get_config_dir() / "target_skus.json").exists():
                    import subprocess
                    from pathlib import Path
                    project_root = Path(__file__).resolve().parent.parent.parent
                    subprocess.run([sys.executable, str(project_root / "refactor_configs.py")], check=True)

            self.target_skus, self.general_skus, self.tax_rates, self.layouts, self.tax_profiles, self.logo_paths, self.store_profiles = load_configs_gui()
            self.cart_builder = CartBuilder(self.target_skus, self.general_skus)
            self.tax_engine = TaxEngine(self.tax_rates, self.tax_profiles)
            self.payment_matcher = PaymentMatcher(self.layouts)
            self.renderer = LayoutRenderer(self.layouts, self.logo_paths)
        except Exception as e:
            QMessageBox.critical(self, "加载错误", f"Failed to load or generate configs: {str(e)}")

    def reload_data(self):
        self.load_data()
        self.populate_lists()
        QMessageBox.information(self, "成功", "配置已重新加载。")

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        config_widget = QWidget()
        form = QFormLayout(config_widget)

        self.lst_targets = QListWidget()
        self.lst_targets.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_targets.setMinimumHeight(100)
        form.addRow("目标商品:", self.lst_targets)

        self.cb_qty_mode = QComboBox()
        self.cb_qty_mode.addItems(["固定", "区间"])
        form.addRow("目标数量模式:", self.cb_qty_mode)

        self.sp_qty_fixed = QSpinBox()
        self.sp_qty_fixed.setRange(1, 100)

        self.sp_qty_min = QSpinBox()
        self.sp_qty_min.setRange(1, 100)
        self.sp_qty_max = QSpinBox()
        self.sp_qty_max.setRange(1, 100)
        self.sp_qty_max.setValue(2)

        self.qty_widget = QStackedWidget()
        w1 = QWidget()
        l1 = QHBoxLayout(w1); l1.setContentsMargins(0,0,0,0)
        l1.addWidget(self.sp_qty_fixed)
        self.qty_widget.addWidget(w1)

        w2 = QWidget()
        l2 = QHBoxLayout(w2); l2.setContentsMargins(0,0,0,0)
        l2.addWidget(QLabel("最小:"))
        l2.addWidget(self.sp_qty_min)
        l2.addWidget(QLabel("最大:"))
        l2.addWidget(self.sp_qty_max)
        self.qty_widget.addWidget(w2)

        form.addRow("目标数量 (固定/最大):", self.qty_widget)
        self.cb_qty_mode.currentTextChanged.connect(self.on_qty_mode_changed)

        self.cb_filler_strategy = QComboBox()
        self.cb_filler_strategy.addItems(["智能关联", "随机", "不凑单"])
        form.addRow("凑单策略:", self.cb_filler_strategy)

        self.sp_filler_min = QSpinBox()
        self.sp_filler_min.setRange(2, 50)
        self.sp_filler_max = QSpinBox()
        self.sp_filler_max.setRange(2, 50)
        self.sp_filler_max.setValue(5)

        filler_layout = QHBoxLayout()
        filler_layout.addWidget(self.sp_filler_min)
        filler_layout.addWidget(QLabel("-"))
        filler_layout.addWidget(self.sp_filler_max)
        form.addRow("凑单数量范围:", filler_layout)

        self.chk_affinity = QCheckBox("强制场景关联")
        self.chk_affinity.setChecked(True)
        form.addRow("", self.chk_affinity)

        self.lst_states = QListWidget()
        self.lst_states.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_states.setMinimumHeight(80)
        self.lst_states.itemSelectionChanged.connect(self.on_state_selected)
        form.addRow("州/省筛选:", self.lst_states)

        self.lst_stores = QListWidget()
        self.lst_stores.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lst_stores.setMinimumHeight(80)
        form.addRow("商家筛选:", self.lst_stores)

        self.le_registers = QLineEdit("01,02,03,04,05")
        form.addRow("收银台池:", self.le_registers)

        self.cb_reg_mode = QComboBox()
        self.cb_reg_mode.addItems(["随机", "轮询", "固定"])
        form.addRow("收银台模式:", self.cb_reg_mode)

        self.sp_void = QDoubleSpinBox()
        self.sp_void.setRange(0.0, 0.3)
        self.sp_void.setSingleStep(0.01)
        self.sp_void.setValue(0.05)
        form.addRow("作废比例:", self.sp_void)

        self.sp_return = QDoubleSpinBox()
        self.sp_return.setRange(0.0, 0.3)
        self.sp_return.setSingleStep(0.01)
        self.sp_return.setValue(0.02)
        form.addRow("退货比例:", self.sp_return)

        time_group = QGroupBox("时间设置")
        time_layout = QFormLayout(time_group)
        self.cb_time_mode = QComboBox()
        self.cb_time_mode.addItems(["最近", "固定", "区间"])
        time_layout.addRow("时间模式:", self.cb_time_mode)

        self.dt_fixed = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_fixed.setCalendarPopup(True)
        self.dt_start = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.dt_start.setCalendarPopup(True)
        self.dt_end = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_end.setCalendarPopup(True)

        self.lbl_recent_hint = QLabel("自动生成过去 7 天内的随机时间")

        self.time_stack = QStackedWidget()
        t1 = QWidget(); tl1 = QVBoxLayout(t1); tl1.addWidget(self.lbl_recent_hint); tl1.setContentsMargins(0,0,0,0); self.time_stack.addWidget(t1)
        t2 = QWidget(); tl2 = QFormLayout(t2); tl2.addRow("固定时间:", self.dt_fixed); tl2.setContentsMargins(0,0,0,0); self.time_stack.addWidget(t2)
        t3 = QWidget(); tl3 = QFormLayout(t3); tl3.addRow("起始时间:", self.dt_start); tl3.addRow("结束时间:", self.dt_end); tl3.setContentsMargins(0,0,0,0); self.time_stack.addWidget(t3)

        time_layout.addRow(self.time_stack)
        self.cb_time_mode.currentTextChanged.connect(self.on_time_mode_changed)
        form.addRow(time_group)

        self.cb_payment = QComboBox()
        self.cb_payment.addItems(["自动", "现金", "刷卡"])
        form.addRow("支付方式:", self.cb_payment)

        self.cb_output = QComboBox()
        self.cb_output.addItems(["保存为图片(PNG)", "直接打印"])
        form.addRow("输出格式:", self.cb_output)

        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, 1000)
        form.addRow("生成数量:", self.sp_count)

        btn_layout = QHBoxLayout()
        self.btn_validate = QPushButton("校验配置")
        self.btn_preview = QPushButton("预览")
        self.btn_batch = QPushButton("批量生成")

        btn_layout.addWidget(self.btn_validate)
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_batch)
        form.addRow(btn_layout)

        self.btn_validate.clicked.connect(self.validate_config)
        self.btn_preview.clicked.connect(self.do_preview)
        self.btn_batch.clicked.connect(self.do_batch)

        scroll.setWidget(config_widget)
        left_layout.addWidget(scroll)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.lbl_preview = QLabel("预览将显示在这里。")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll_preview = QScrollArea()
        scroll_preview.setWidgetResizable(True)
        scroll_preview.setWidget(self.lbl_preview)

        right_layout.addWidget(scroll_preview)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])

        self.populate_lists()

    def on_qty_mode_changed(self, text):
        if text == "固定":
            self.qty_widget.setCurrentIndex(0)
        else:
            self.qty_widget.setCurrentIndex(1)

    def on_time_mode_changed(self, text):
        if text == "最近":
            self.time_stack.setCurrentIndex(0)
        elif text == "固定":
            self.time_stack.setCurrentIndex(1)
        else:
            self.time_stack.setCurrentIndex(2)

    def populate_lists(self):
        self.lst_targets.clear()
        for t in self.target_skus:
            item = QListWidgetItem(f"{t.name} (${t.rebate_price})")
            item.setData(Qt.ItemDataRole.UserRole, t.sku_id)
            self.lst_targets.addItem(item)

        self.lst_states.clear()
        self.lst_states.addItem(QListWidgetItem("所有(All)"))
        for st in sorted(self.tax_rates.keys()):
            self.lst_states.addItem(st)

        self.on_state_selected()

    def on_state_selected(self):
        selected_states = [i.text() for i in self.lst_states.selectedItems() if i.text() != "所有(All)"]
        self.lst_stores.clear()
        self.lst_stores.addItem("所有(All)")

        # Sort stores by name alphabetically
        sorted_profiles = sorted(self.store_profiles.items(), key=lambda x: x[1].name)

        for store_id, prof in sorted_profiles:
            if not selected_states:
                item = QListWidgetItem(prof.name)
                item.setData(Qt.ItemDataRole.UserRole, store_id)
                self.lst_stores.addItem(item)
            else:
                for st in selected_states:
                    if st in prof.region_whitelist:
                        item = QListWidgetItem(prof.name)
                        item.setData(Qt.ItemDataRole.UserRole, store_id)
                        self.lst_stores.addItem(item)
                        break

    def get_config(self) -> RebateJobConfig:
        targets = [i.data(Qt.ItemDataRole.UserRole) for i in self.lst_targets.selectedItems()]
        if not targets:
            raise ValueError("请至少选择一个目标商品。")

        stores = []
        for i in self.lst_stores.selectedItems():
            if i.text() == "所有(All)":
                stores = None
                break
            else:
                s_id = i.data(Qt.ItemDataRole.UserRole)
                if s_id: stores.append(s_id)

        states = [i.text() for i in self.lst_states.selectedItems()]
        if not states or "所有(All)" in states:
            states = None

        regs = [r.strip() for r in self.le_registers.text().split(",") if r.strip()]

        tmode = "recent" if self.cb_time_mode.currentText() == "最近" else ("fixed" if self.cb_time_mode.currentText() == "固定" else "range")
        qmode = "fixed" if self.cb_qty_mode.currentText() == "固定" else "range"
        fstrat = "smart" if self.cb_filler_strategy.currentText() == "智能关联" else ("random" if self.cb_filler_strategy.currentText() == "随机" else "none")
        pmode = "auto" if self.cb_payment.currentText() == "自动" else ("cash" if self.cb_payment.currentText() == "现金" else "card")
        outformat = "png" if self.cb_output.currentText() == "保存为图片(PNG)" else "direct_print"

        cfg = RebateJobConfig(
            target_skus=targets,
            target_qty_mode=qmode,
            target_qty_value=self.sp_qty_fixed.value() if qmode == "fixed" else (self.sp_qty_min.value(), self.sp_qty_max.value()),
            filler_strategy=fstrat,
            filler_count_range=(self.sp_filler_min.value(), self.sp_filler_max.value()),
            affinity_enforce=self.chk_affinity.isChecked(),
            store_filter=stores,
            state_filter=states,
            register_pool=regs,
            register_mode="random",
            void_ratio=self.sp_void.value(),
            return_ratio=self.sp_return.value(),
            payment_mode=pmode,
            output_format=outformat,
            count=self.sp_count.value(),
            time_mode=tmode,
            time_fixed=self.dt_fixed.dateTime().toPyDateTime().isoformat() if tmode == "fixed" else None,
            time_range_start=self.dt_start.dateTime().toPyDateTime().isoformat() if tmode == "range" else None,
            time_range_end=self.dt_end.dateTime().toPyDateTime().isoformat() if tmode == "range" else None
        )
        return cfg

    def validate_config(self):
        try:
            cfg = self.get_config()
            QMessageBox.information(self, "校验通过", "配置有效，随时可以生成！")
        except Exception as e:
            QMessageBox.warning(self, "配置无效", str(e))

    def generate_single(self, config: RebateJobConfig, job_id: str, prev_time=None):
        cart = self.cart_builder.build_cart(config)
        cart = self.tax_engine.calculate_taxes(cart)
        payment = self.payment_matcher.generate_payment(config, cart)

        register_id = random.choice(config.register_pool)
        if random.random() < config.void_ratio:
            self.txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "VOID", job_id)
        if random.random() < config.return_ratio:
            self.txn_lock.allocate_abnormal(cart.store_id, register_id, 1, "RETURN", job_id)

        txn_seq, ts = self.txn_lock.next_seq(cart.store_id, register_id, job_id)

        prof = self.store_profiles.get(cart.store_id)
        if not prof:
            raise ValueError(f"缺少商家配置: {cart.store_id}")

        addrs = prof.addresses.get(cart.state_code, [])
        if not addrs:
            raise ValueError(f"商家 {prof.name} 在 {cart.state_code} 州不可用")

        addr_dict = random.choice(addrs)
        address = StoreAddress(**addr_dict)

        layout = self.layouts[cart.store_id]

        dt_start = datetime.fromisoformat(config.time_range_start) if config.time_range_start else None
        dt_end = datetime.fromisoformat(config.time_range_end) if config.time_range_end else None
        dt_fixed = datetime.fromisoformat(config.time_fixed) if config.time_fixed else None

        from datetime import timedelta
        base_time = generate_timestamp(config.time_mode, dt_fixed, dt_start, dt_end)
        if prev_time and config.time_mode != "fixed":
            if base_time <= prev_time:
                base_time = prev_time + timedelta(seconds=random.randint(60, 1800))
                if dt_end and base_time > dt_end:
                    base_time = dt_end - timedelta(seconds=random.randint(1, 10))

        ts_str = base_time.strftime(layout.footer.time_format)

        from models.core import ReceiptData
        receipt = ReceiptData(
            job_id=job_id,
            cart=cart,
            payment=payment,
            register_id=register_id,
            txn_seq=txn_seq,
            timestamp=ts_str,
            address=address
        )

        PreRenderSanityCheck.verify(receipt.cart, receipt.payment, config.affinity_enforce)
        return receipt, register_id, txn_seq, base_time

    def do_preview(self):
        try:
            config = self.get_config()
            config.output_format = "png"

            job_id = "PREVIEW-001"
            receipt, reg_id, seq, _ = self.generate_single(config, job_id)

            img = self.renderer.render_png(receipt)

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
            QMessageBox.critical(self, "预览错误", str(e))

    def do_batch(self):
        try:
            config = self.get_config()
            job_id = f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            batch_dir = str(get_next_batch_dir())

            png_printer = PngPrinter(batch_dir)
            direct_printer = DirectPrinter(batch_dir)

            success_count = 0
            prev_time = None
            for i in range(config.count):
                receipt, reg_id, seq, p_time = self.generate_single(config, job_id, prev_time)
                prev_time = p_time

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

            QMessageBox.information(self, "批量生成完成", f"成功生成 {success_count} 张收据至 {batch_dir}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "批量生成错误", str(e))
