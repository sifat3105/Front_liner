from __future__ import annotations

import re
from typing import Dict, Any, List, Optional

from django.db.models import Q
from langchain_core.tools import tool

from apps.inventory.models import Product, Stock
from apps.vendor.models import Vendor


def _tokenize_query(query: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", (query or "").lower())
    return [t for t in tokens if len(t) > 1]


def _build_product_query(query: str) -> Q:
    query = (query or "").strip()
    if not query:
        return Q()

    tokens = _tokenize_query(query)
    q = (
        Q(product__icontains=query)
        | Q(brand__icontains=query)
        | Q(sku__icontains=query)
        | Q(items__sku__icontains=query)
        | Q(items__size__icontains=query)
        | Q(items__color__icontains=query)
    )

    for tok in tokens:
        q |= (
            Q(product__icontains=tok)
            | Q(brand__icontains=tok)
            | Q(sku__icontains=tok)
            | Q(items__sku__icontains=tok)
            | Q(items__size__icontains=tok)
            | Q(items__color__icontains=tok)
        )

    return q


def _get_vendor_queryset(user_id: int, vendor_id: Optional[int] = None):
    qs = Vendor.objects.filter(owner_id=user_id, is_active=True)
    if vendor_id:
        qs = qs.filter(id=vendor_id)
    return qs


def _serialize_product(product: Product, query_tokens: List[str], variant_limit: int) -> Dict[str, Any]:
    items = list(product.items.all())

    matched_items = []
    if query_tokens:
        for item in items:
            size = (item.size or "").lower()
            color = (item.color or "").lower()
            sku = (item.sku or "").lower()
            if any(tok in size or tok in color or tok in sku for tok in query_tokens):
                matched_items.append(item)

    if matched_items:
        items = matched_items

    variants = []
    for idx, item in enumerate(items):
        if idx >= variant_limit:
            break
        variants.append({
            "sku": item.sku,
            "size": item.size,
            "color": item.color,
            "quantity": item.quantity or 0,
            "sell_price": str(item.sell_price) if item.sell_price is not None else None,
        })

    prices = [item.sell_price for item in items if item.sell_price is not None]
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None

    stock_balance = None
    try:
        if hasattr(product, "stock") and product.stock:
            stock_balance = product.stock.balance
    except Stock.DoesNotExist:
        stock_balance = None

    if stock_balance is None:
        stock_balance = sum((item.quantity or 0) for item in product.items.all())

    image_url = None
    if getattr(product, "image", None):
        try:
            image_url = product.image.url
        except Exception:
            image_url = None

    return {
        "id": product.id,
        "vendor_id": product.vendor_id,
        "name": product.product,
        "brand": product.brand,
        "sku": product.sku,
        "status": product.status,
        "stock_balance": stock_balance,
        "price_min": str(min_price) if min_price is not None else None,
        "price_max": str(max_price) if max_price is not None else None,
        "image_url": image_url,
        "variants": variants,
    }


def _search_inventory_products(
    user_id: int,
    query: str = "",
    limit: int = 8,
    vendor_id: Optional[int] = None,
    status: Optional[str] = "published",
    variant_limit: int = 5,
) -> Dict[str, Any]:
    if not user_id:
        return {"error": "user_id is required"}

    vendors = _get_vendor_queryset(user_id, vendor_id=vendor_id)
    if not vendors.exists():
        return {"error": "No active vendor found for this user"}

    qs = (
        Product.objects
        .filter(vendor__in=vendors)
        .select_related("vendor", "stock")
        .prefetch_related("items")
        .order_by("-created")
    )

    if status:
        qs = qs.filter(status=status)

    if query:
        qs = qs.filter(_build_product_query(query)).distinct()

    total = qs.count()
    qs = qs[:max(1, min(limit, 50))]

    query_tokens = _tokenize_query(query)
    products = [
        _serialize_product(p, query_tokens=query_tokens, variant_limit=variant_limit)
        for p in qs
    ]

    return {
        "success": True,
        "query": query,
        "total_matches": total,
        "returned": len(products),
        "products": products,
    }


@tool
def search_inventory_products(
    user_id: int,
    query: str = "",
    limit: int = 8,
    vendor_id: Optional[int] = None,
    status: Optional[str] = "published",
    variant_limit: int = 5,
) -> Dict[str, Any]:
    """
    Search inventory products by query (name/brand/SKU/variant).
    Returns a compact list with stock balance and variant info.
    """
    return _search_inventory_products(
        user_id=user_id,
        query=query,
        limit=limit,
        vendor_id=vendor_id,
        status=status,
        variant_limit=variant_limit,
    )


@tool
def list_inventory_products(
    user_id: int,
    limit: int = 8,
    vendor_id: Optional[int] = None,
    status: Optional[str] = "published",
) -> Dict[str, Any]:
    """
    List inventory products for a user (optionally filtered by vendor/status).
    """
    return _search_inventory_products(
        user_id=user_id,
        query="",
        limit=limit,
        vendor_id=vendor_id,
        status=status,
        variant_limit=5,
    )
