from __future__ import annotations

from collections import Counter
from typing import Any

from .preprocess import O2CDataStore


def top_products_by_billing_count(
    store: O2CDataStore, top_n: int = 5
) -> dict[str, list[dict[str, Any]]]:
    ranked = store.billing_count_by_material.most_common(top_n)
    results: list[dict[str, Any]] = []

    for material, billing_count in ranked:
        results.append(
            {
                "product_id": material,
                "product_name": store.product_name_by_id.get(material, ""),
                "billing_count": billing_count,
            }
        )
    return {"rows": results}


def trace_billing_document_flow(
    store: O2CDataStore, billing_document_id: str
) -> dict[str, Any]:
    billing_items = store.billing_items_by_doc.get(billing_document_id, [])
    if not billing_items:
        return {"billing_document_id": billing_document_id, "items": [], "flow": []}

    billing_header = store.billing_header_by_doc.get(billing_document_id, {})
    accounting_document = str(billing_header.get("accountingDocument", "")).strip()
    journal_entries = store.journal_entries_by_reference_doc.get(billing_document_id, [])
    if not journal_entries and accounting_document:
        journal_entries = store.journal_entries_by_accounting_doc.get(accounting_document, [])

    payment_rows = (
        store.payments_by_accounting_doc.get(accounting_document, [])
        if accounting_document
        else []
    )

    flow: list[dict[str, str]] = []
    for item in billing_items:
        delivery_id = str(item.get("referenceSdDocument", "")).strip()
        delivery_items = store.delivery_by_id.get(delivery_id, [])
        sales_ids = sorted(
            {
                str(delivery_row.get("referenceSdDocument", "")).strip()
                for delivery_row in delivery_items
                if str(delivery_row.get("referenceSdDocument", "")).strip()
            }
        )

        flow.append(
            {
                "billing_document": billing_document_id,
                "billing_item": str(item.get("billingDocumentItem", "")).strip(),
                "delivery_document": delivery_id,
                "sales_orders": ",".join(sales_ids),
                "material": str(item.get("material", "")).strip(),
                "accounting_document": accounting_document,
                "journal_entries_count": str(len(journal_entries)),
            }
        )

    return {
        "billing_document_id": billing_document_id,
        "accounting_document": accounting_document,
        "items": billing_items,
        "flow": flow,
        "journal_entries": journal_entries,
        "payments": payment_rows,
        "summary": {
            "billing_items_count": len(billing_items),
            "journal_entries_count": len(journal_entries),
            "payments_count": len(payment_rows),
        },
    }


def broken_flow_detection(store: O2CDataStore) -> dict[str, Any]:
    delivered_sales_orders = set(store.delivery_items_by_sales_ref.keys())
    delivered_not_billed: list[dict[str, Any]] = []

    for sales_order in sorted(delivered_sales_orders):
        delivery_rows = store.delivery_items_by_sales_ref.get(sales_order, [])
        delivery_docs = {
            str(row.get("deliveryDocument", "")).strip()
            for row in delivery_rows
            if str(row.get("deliveryDocument", "")).strip()
        }

        billing_hits = sum(
            len(store.billing_items_by_delivery_ref.get(delivery_doc, []))
            for delivery_doc in delivery_docs
        )
        if billing_hits == 0:
            delivered_not_billed.append(
                {
                    "sales_order": sales_order,
                    "delivery_documents": sorted(delivery_docs),
                }
            )

    billed_without_delivery: list[dict[str, Any]] = []
    for delivery_ref, billing_rows in store.billing_items_by_delivery_ref.items():
        if delivery_ref in store.delivery_by_id:
            continue
        billed_without_delivery.append(
            {
                "delivery_reference": delivery_ref,
                "billing_documents": sorted(
                    {
                        str(row.get("billingDocument", "")).strip()
                        for row in billing_rows
                        if str(row.get("billingDocument", "")).strip()
                    }
                ),
            }
        )

    return {
        "delivered_not_billed": delivered_not_billed,
        "billed_without_delivery": billed_without_delivery,
        "summary": {
            "delivered_not_billed_count": len(delivered_not_billed),
            "billed_without_delivery_count": len(billed_without_delivery),
        },
    }


ALLOWED_TEMPLATES = {
    "top_products_by_billing_count": top_products_by_billing_count,
    "trace_billing_document_flow": trace_billing_document_flow,
    "broken_flow_detection": broken_flow_detection,
}
