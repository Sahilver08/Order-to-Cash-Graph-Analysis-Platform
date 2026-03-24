from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/graph", tags=["graph"])


def _build_graph_payload(store: Any) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    adjacency: dict[str, list[str]] = defaultdict(list)

    for row in store.sales_order_items:
        node_id = f"SO:{str(row.get('salesOrder', '')).strip()}"
        if node_id == "SO:":
            continue
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "type": "sales_order",
                "metadata": {
                    "entity": "Sales Order",
                    "salesOrder": str(row.get("salesOrder", "")).strip(),
                    "material": str(row.get("material", "")).strip(),
                    "requestedQuantity": str(row.get("requestedQuantity", "")).strip(),
                    "netAmount": str(row.get("netAmount", "")).strip(),
                    "transactionCurrency": str(row.get("transactionCurrency", "")).strip(),
                    "productionPlant": str(row.get("productionPlant", "")).strip(),
                },
            }

        product = str(row.get("material", "")).strip()
        if product:
            product_id = f"PR:{product}"
            if product_id not in nodes:
                nodes[product_id] = {
                    "id": product_id,
                    "type": "product",
                    "metadata": {
                        "entity": "Product",
                        "product": product,
                        "productName": store.product_name_by_id.get(product, ""),
                    },
                }
            edges.append({"source": node_id, "target": product_id, "label": "SO_ITEM_TO_PRODUCT"})
            adjacency[node_id].append(product_id)

    for row in store.outbound_delivery_items:
        delivery = str(row.get("deliveryDocument", "")).strip()
        sales_order = str(row.get("referenceSdDocument", "")).strip()
        if not delivery:
            continue

        delivery_id = f"DL:{delivery}"
        if delivery_id not in nodes:
            nodes[delivery_id] = {
                "id": delivery_id,
                "type": "delivery_document",
                "metadata": {
                    "entity": "Delivery",
                    "deliveryDocument": delivery,
                    "plant": str(row.get("plant", "")).strip(),
                    "storageLocation": str(row.get("storageLocation", "")).strip(),
                    "actualDeliveryQuantity": str(row.get("actualDeliveryQuantity", "")).strip(),
                    "deliveryQuantityUnit": str(row.get("deliveryQuantityUnit", "")).strip(),
                    "referenceSalesOrder": sales_order,
                },
            }

        if sales_order:
            so_id = f"SO:{sales_order}"
            if so_id in nodes:
                edges.append({"source": so_id, "target": delivery_id, "label": "SO_TO_DL"})
                adjacency[so_id].append(delivery_id)

    for row in store.billing_document_items:
        billing = str(row.get("billingDocument", "")).strip()
        delivery_ref = str(row.get("referenceSdDocument", "")).strip()
        if not billing:
            continue

        billing_id = f"BL:{billing}"
        if billing_id not in nodes:
            header = next(
                (
                    x
                    for x in store.billing_document_headers
                    if str(x.get("billingDocument", "")).strip() == billing
                ),
                {},
            )
            nodes[billing_id] = {
                "id": billing_id,
                "type": "billing_document",
                "metadata": {
                    "entity": "Billing",
                    "billingDocument": billing,
                    "material": str(row.get("material", "")).strip(),
                    "billingQuantity": str(row.get("billingQuantity", "")).strip(),
                    "netAmount": str(row.get("netAmount", "")).strip(),
                    "transactionCurrency": str(row.get("transactionCurrency", "")).strip(),
                    "soldToParty": str(header.get("soldToParty", "")).strip(),
                    "billingDate": str(header.get("billingDocumentDate", "")).strip(),
                },
            }

            sold_to_party = str(header.get("soldToParty", "")).strip()
            if sold_to_party:
                customer_id = f"CU:{sold_to_party}"
                if customer_id not in nodes:
                    nodes[customer_id] = {
                        "id": customer_id,
                        "type": "customer",
                        "metadata": {
                            "entity": "Customer",
                            "customer": sold_to_party,
                            "customerName": store.customer_name_by_id.get(sold_to_party, ""),
                        },
                    }
                edges.append({"source": customer_id, "target": billing_id, "label": "CUSTOMER_TO_BILLING"})
                adjacency[customer_id].append(billing_id)

            accounting_document = str(header.get("accountingDocument", "")).strip()
            if accounting_document:
                journal_id = f"JE:{accounting_document}"
                journal_rows = store.journal_entries_by_accounting_doc.get(accounting_document, [])
                if not journal_rows:
                    journal_rows = store.journal_entries_by_reference_doc.get(billing, [])
                first_journal = journal_rows[0] if journal_rows else {}
                if journal_id not in nodes:
                    nodes[journal_id] = {
                        "id": journal_id,
                        "type": "journal_entry",
                        "metadata": {
                            "entity": "Journal Entry",
                            "accountingDocument": accounting_document,
                            "companyCode": str(first_journal.get("companyCode", "")).strip(),
                            "fiscalYear": str(first_journal.get("fiscalYear", "")).strip(),
                            "referenceDocument": str(first_journal.get("referenceDocument", "")).strip(),
                        },
                    }
                edges.append({"source": billing_id, "target": journal_id, "label": "BL_TO_JE"})
                adjacency[billing_id].append(journal_id)

                payment_rows = store.payments_by_accounting_doc.get(accounting_document, [])
                for pay_row in payment_rows[:3]:
                    payment_doc = str(pay_row.get("accountingDocument", "")).strip()
                    if not payment_doc:
                        continue
                    payment_id = f"PY:{payment_doc}"
                    if payment_id not in nodes:
                        nodes[payment_id] = {
                            "id": payment_id,
                            "type": "payment",
                            "metadata": {
                                "entity": "Payment",
                                "accountingDocument": payment_doc,
                                "clearingDate": str(pay_row.get("clearingDate", "")).strip(),
                                "amountInTransactionCurrency": str(
                                    pay_row.get("amountInTransactionCurrency", "")
                                ).strip(),
                                "transactionCurrency": str(pay_row.get("transactionCurrency", "")).strip(),
                                "customer": str(pay_row.get("customer", "")).strip(),
                            },
                        }
                    edges.append({"source": journal_id, "target": payment_id, "label": "JE_TO_PAYMENT"})
                    adjacency[journal_id].append(payment_id)

        if delivery_ref:
            delivery_id = f"DL:{delivery_ref}"
            if delivery_id in nodes:
                edges.append({"source": delivery_id, "target": billing_id, "label": "DL_TO_BL"})
                adjacency[delivery_id].append(billing_id)

    # Optional address attachment for a few visible customer nodes.
    for node_id, node_data in list(nodes.items()):
        if node_data.get("type") != "customer":
            continue
        customer = str(node_data.get("metadata", {}).get("customer", "")).strip()
        if not customer:
            continue

        address_rows = store.addresses_by_business_partner.get(customer, [])
        if not address_rows:
            continue
        address_row = address_rows[0]
        address_id_val = str(address_row.get("addressId", "")).strip()
        if not address_id_val:
            continue
        address_id = f"AD:{address_id_val}"
        if address_id not in nodes:
            nodes[address_id] = {
                "id": address_id,
                "type": "address",
                "metadata": {
                    "entity": "Address",
                    "addressId": address_id_val,
                    "cityName": str(address_row.get("cityName", "")).strip(),
                    "country": str(address_row.get("country", "")).strip(),
                    "postalCode": str(address_row.get("postalCode", "")).strip(),
                },
            }
        edges.append({"source": node_id, "target": address_id, "label": "CUSTOMER_TO_ADDRESS"})
        adjacency[node_id].append(address_id)

    return {"nodes": list(nodes.values()), "edges": edges, "adjacency": dict(adjacency)}


@router.get("/overview")
def get_graph_overview(request: Request) -> dict[str, Any]:
    store = request.app.state.data_store
    graph = _build_graph_payload(store)
    return {
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "summary": {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
        },
    }


@router.get("/expand/{node_id}")
def expand_node(node_id: str, request: Request) -> dict[str, Any]:
    store = request.app.state.data_store
    graph = _build_graph_payload(store)
    node_map = {node["id"]: node for node in graph["nodes"]}
    neighbor_ids = graph["adjacency"].get(node_id, [])

    return {
        "node": node_map.get(node_id),
        "neighbors": [node_map[n_id] for n_id in neighbor_ids if n_id in node_map],
        "edges": [e for e in graph["edges"] if e["source"] == node_id],
    }
