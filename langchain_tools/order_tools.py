from __future__ import annotations
from langchain_core.tools import tool
from typing import Dict, Any, List
from datetime import datetime
from django.db import transaction
import re
from decimal import Decimal

from apps.orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


@tool("get_order", description="Fetch an order by order_id and return summary fields with item details.")
def get_order(order_id: str) -> Dict[str, Any]:
    """Fetch an order by order_id and return summary fields with item details."""
    order_id = (order_id or "").strip()

    if not re.fullmatch(r"^[A-Za-z0-9]+-\d+$", order_id):
        return {"error": "Invalid order ID format. Example: BRAND-1001"}

    order = (
        Order.objects
        .select_related("user")
        .prefetch_related("items")
        .filter(order_id=order_id)
        .first()
    )

    if not order:
        return {"error": "Order not found", "order_id": order_id}

    return {
        "order_id": order.order_id,
        "customer": order.customer,
        "location": order.location,
        "contact": order.contact,
        "order_amount": str(order.order_amount),
        "platform": order.platform,
        "order_status": order.order_status,
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "color": item.color,
                "size": item.size,
                "weight": item.weight,
                "notes": item.notes,
            }
            for item in order.items.all()
        ],
    }


@tool("create_order", description="Create a new order with items for a specific user.")
def create_order(
    user_id: int,
    customer: str,
    location: str,
    contact: str,
    platform: str,
    items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a new order with items for a specific user and persist to Order/OrderItem models.
    """

    if not items or not isinstance(items, list):
        return {"error": "Items list is required"}

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    # ---- calculate total amount (example logic) ----
    total_amount = Decimal("0.00")
    for item in items:
        qty = int(item.get("quantity", 1))
        total_amount += Decimal("100.00") * qty  # demo price logic

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                customer=customer,
                location=location,
                contact=contact,
                platform=platform,
                order_amount=total_amount,
                status="PENDING",
                order_status="PENDING",
            )

            order_items = []
            for item in items:
                order_items.append(
                    OrderItem(
                        order=order,
                        product_name=item.get("product_name"),
                        quantity=item.get("quantity", 1),
                        color=item.get("color"),
                        size=item.get("size"),
                        weight=item.get("weight"),
                        notes=item.get("notes"),
                    )
                )

            OrderItem.objects.bulk_create(order_items)

    except Exception as e:
        return {"error": "Order creation failed", "details": str(e)}

    return {
        "success": True,
        "order_id": order.order_id,
        "order_amount": str(order.order_amount),
        "items_count": len(order_items),
        "message": "Order created successfully",
    }

    
