from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class O2CDataStore:
    base_path: Path
    sales_order_items: list[dict[str, Any]] = field(default_factory=list)
    outbound_delivery_items: list[dict[str, Any]] = field(default_factory=list)
    billing_document_items: list[dict[str, Any]] = field(default_factory=list)
    billing_document_headers: list[dict[str, Any]] = field(
        default_factory=list)
    products: list[dict[str, Any]] = field(default_factory=list)
    product_descriptions: list[dict[str, Any]] = field(default_factory=list)
    business_partners: list[dict[str, Any]] = field(default_factory=list)
    business_partner_addresses: list[dict[str, Any]] = field(
        default_factory=list)
    journal_entry_items_ar: list[dict[str, Any]] = field(default_factory=list)
    payments_ar: list[dict[str, Any]] = field(default_factory=list)

    # Indexes for deterministic query templates
    billing_count_by_material: Counter = field(default_factory=Counter)
    delivery_by_id: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    sales_items_by_order: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    billing_items_by_doc: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    billing_items_by_delivery_ref: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    delivery_items_by_sales_ref: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    product_name_by_id: dict[str, str] = field(default_factory=dict)
    billing_header_by_doc: dict[str, dict[str, Any]
                                ] = field(default_factory=dict)
    journal_entries_by_reference_doc: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    journal_entries_by_accounting_doc: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    payments_by_accounting_doc: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    payments_by_customer: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))
    customer_name_by_id: dict[str, str] = field(default_factory=dict)
    addresses_by_business_partner: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list))

    def load(self) -> None:
        self.sales_order_items = _read_jsonl_table(
            self.base_path, "sales_order_items")
        self.outbound_delivery_items = _read_jsonl_table(
            self.base_path, "outbound_delivery_items")
        self.billing_document_items = _read_jsonl_table(
            self.base_path, "billing_document_items")
        self.billing_document_headers = _read_jsonl_table(
            self.base_path, "billing_document_headers")
        self.products = _read_jsonl_table(self.base_path, "products")
        self.product_descriptions = _read_jsonl_table(
            self.base_path, "product_descriptions")
        self.business_partners = _read_jsonl_table(
            self.base_path, "business_partners")
        self.business_partner_addresses = _read_jsonl_table(
            self.base_path, "business_partner_addresses")
        self.journal_entry_items_ar = _read_jsonl_table(
            self.base_path, "journal_entry_items_accounts_receivable")
        self.payments_ar = _read_jsonl_table(
            self.base_path, "payments_accounts_receivable")

        # Build indexes
        self._build_indexes()

    def _build_indexes(self) -> None:
        # billing_count_by_material
        for item in self.billing_document_items:
            material = str(item.get("material", "")).strip()
            if material:
                self.billing_count_by_material[material] += 1

        # delivery_by_id
        for item in self.outbound_delivery_items:
            delivery_id = str(item.get("deliveryDocument", "")).strip()
            if delivery_id:
                self.delivery_by_id[delivery_id].append(item)

        # sales_items_by_order
        for item in self.sales_order_items:
            order_id = str(item.get("salesDocument", "")).strip()
            if order_id:
                self.sales_items_by_order[order_id].append(item)

        # billing_items_by_doc
        for item in self.billing_document_items:
            doc_id = str(item.get("billingDocument", "")).strip()
            if doc_id:
                self.billing_items_by_doc[doc_id].append(item)

        # billing_items_by_delivery_ref
        for item in self.billing_document_items:
            ref = str(item.get("referenceSdDocument", "")).strip()
            if ref:
                self.billing_items_by_delivery_ref[ref].append(item)

        # delivery_items_by_sales_ref
        for item in self.outbound_delivery_items:
            ref = str(item.get("referenceSdDocument", "")).strip()
            if ref:
                self.delivery_items_by_sales_ref[ref].append(item)

        # product_name_by_id
        for item in self.products:
            product_id = str(item.get("product", "")).strip()
            name = str(item.get("productDescription", "")).strip()
            if product_id:
                self.product_name_by_id[product_id] = name

        # billing_header_by_doc
        for item in self.billing_document_headers:
            doc_id = str(item.get("billingDocument", "")).strip()
            if doc_id:
                self.billing_header_by_doc[doc_id] = item

        # journal_entries_by_reference_doc and by_accounting_doc
        for item in self.journal_entry_items_ar:
            ref_doc = str(item.get("referenceDocument", "")).strip()
            acc_doc = str(item.get("accountingDocument", "")).strip()
            if ref_doc:
                self.journal_entries_by_reference_doc[ref_doc].append(item)
            if acc_doc:
                self.journal_entries_by_accounting_doc[acc_doc].append(item)

        # payments_by_accounting_doc and by_customer
        for item in self.payments_ar:
            acc_doc = str(item.get("accountingDocument", "")).strip()
            customer = str(item.get("customer", "")).strip()
            if acc_doc:
                self.payments_by_accounting_doc[acc_doc].append(item)
            if customer:
                self.payments_by_customer[customer].append(item)

        # customer_name_by_id
        for item in self.business_partners:
            customer_id = str(item.get("businessPartner", "")).strip()
            name = str(item.get("businessPartnerName", "")).strip()
            if customer_id:
                self.customer_name_by_id[customer_id] = name

        # addresses_by_business_partner
        for item in self.business_partner_addresses:
            bp_id = str(item.get("businessPartner", "")).strip()
            if bp_id:
                self.addresses_by_business_partner[bp_id].append(item)
        self._build_indexes()

    def _build_indexes(self) -> None:
        self.billing_count_by_material.clear()
        self.delivery_by_id.clear()
        self.sales_items_by_order.clear()
        self.billing_items_by_doc.clear()
        self.billing_items_by_delivery_ref.clear()
        self.delivery_items_by_sales_ref.clear()
        self.product_name_by_id.clear()
        self.billing_header_by_doc.clear()
        self.journal_entries_by_reference_doc.clear()
        self.journal_entries_by_accounting_doc.clear()
        self.payments_by_accounting_doc.clear()
        self.payments_by_customer.clear()
        self.customer_name_by_id.clear()
        self.addresses_by_business_partner.clear()

        for row in self.product_descriptions:
            if str(row.get("language", "")).upper() != "EN":
                continue
            product = str(row.get("product", "")).strip()
            if not product:
                continue
            self.product_name_by_id[product] = str(
                row.get("productDescription", "")).strip()

        for row in self.billing_document_items:
            material = str(row.get("material", "")).strip()
            if material:
                self.billing_count_by_material[material] += 1

            billing_doc = str(row.get("billingDocument", "")).strip()
            if billing_doc:
                self.billing_items_by_doc[billing_doc].append(row)

            # In this dataset this usually points to delivery document id.
            delivery_ref = str(row.get("referenceSdDocument", "")).strip()
            if delivery_ref:
                self.billing_items_by_delivery_ref[delivery_ref].append(row)

        for row in self.billing_document_headers:
            billing_doc = str(row.get("billingDocument", "")).strip()
            if billing_doc:
                self.billing_header_by_doc[billing_doc] = row

        for row in self.outbound_delivery_items:
            delivery_doc = str(row.get("deliveryDocument", "")).strip()
            if delivery_doc:
                self.delivery_by_id[delivery_doc].append(row)

            sales_ref = str(row.get("referenceSdDocument", "")).strip()
            if sales_ref:
                self.delivery_items_by_sales_ref[sales_ref].append(row)

        for row in self.sales_order_items:
            sales_order = str(row.get("salesOrder", "")).strip()
            if sales_order:
                self.sales_items_by_order[sales_order].append(row)

        for row in self.business_partners:
            customer_id = str(row.get("customer", "")).strip()
            full_name = str(row.get("businessPartnerFullName", "")).strip()
            fallback_name = str(row.get("businessPartnerName", "")).strip()
            if customer_id:
                self.customer_name_by_id[customer_id] = full_name or fallback_name

            business_partner = str(row.get("businessPartner", "")).strip()
            if business_partner and business_partner != customer_id and customer_id:
                self.customer_name_by_id.setdefault(
                    customer_id, full_name or fallback_name)

        for row in self.business_partner_addresses:
            business_partner = str(row.get("businessPartner", "")).strip()
            if business_partner:
                self.addresses_by_business_partner[business_partner].append(
                    row)

        for row in self.journal_entry_items_ar:
            reference_doc = str(row.get("referenceDocument", "")).strip()
            accounting_doc = str(row.get("accountingDocument", "")).strip()
            if reference_doc:
                self.journal_entries_by_reference_doc[reference_doc].append(
                    row)
            if accounting_doc:
                self.journal_entries_by_accounting_doc[accounting_doc].append(
                    row)

        for row in self.payments_ar:
            accounting_doc = str(row.get("clearingAccountingDocument", "")).strip() or str(
                row.get("accountingDocument", "")
            ).strip()
            customer_id = str(row.get("customer", "")).strip()
            if accounting_doc:
                self.payments_by_accounting_doc[accounting_doc].append(row)
            if customer_id:
                self.payments_by_customer[customer_id].append(row)


def _read_jsonl_table(base_path: Path, table_name: str) -> list[dict[str, Any]]:
    table_dir = base_path / table_name
    if not table_dir.exists():
        return []

    rows: list[dict[str, Any]] = []
    for file_path in sorted(table_dir.glob("*.jsonl")):
        with file_path.open("r", encoding="utf-8") as file_handle:
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    return rows
