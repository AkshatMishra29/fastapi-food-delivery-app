from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# ==========================================
# MOCK DATABASE & GLOBALS
# ==========================================
menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Pepperoni Pizza", "price": 300, "category": "Pizza", "is_available": True},
    {"id": 3, "name": "Veggie Burger", "price": 150, "category": "Burger", "is_available": False},
    {"id": 4, "name": "Chicken Burger", "price": 200, "category": "Burger", "is_available": True},
    {"id": 5, "name": "Cold Coffee", "price": 90, "category": "Drink", "is_available": True},
    {"id": 6, "name": "Chocolate Brownie", "price": 120, "category": "Dessert", "is_available": True}
]

orders = []
order_counter = 1
cart = [] # Added for Q14 and Q15

# ==========================================
# PYDANTIC MODELS
# ==========================================
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = Field(default="delivery")

class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def find_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price: int, quantity: int, order_type: str):
    total = price * quantity
    if order_type.lower() == "delivery":
        total += 30
    return total

def filter_menu_logic(category: Optional[str], max_price: Optional[int], is_available: Optional[bool]):
    filtered_items = menu
    if category is not None:
        filtered_items = [item for item in filtered_items if item["category"].lower() == category.lower()]
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] <= max_price]
    if is_available is not None:
        filtered_items = [item for item in filtered_items if item["is_available"] == is_available]
    return filtered_items

# ==========================================
# ENDPOINTS (STRICT ROUTE ORDER)
# ==========================================

# --- Q1: Home ---
@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}

# --- Q2: List Menu ---
@app.get("/menu")
def get_menu():
    return {"total": len(menu), "items": menu}

# --- Q5: Summary ---
@app.get("/menu/summary")
def get_menu_summary():
    available_count = sum(1 for item in menu if item["is_available"])
    return {
        "total_items": len(menu),
        "available_count": available_count,
        "unavailable_count": len(menu) - available_count,
        "categories": list({item["category"] for item in menu})
    }

# --- Q10: Filter Menu ---
@app.get("/menu/filter")
def filter_menu(category: Optional[str] = None, max_price: Optional[int] = None, is_available: Optional[bool] = None):
    results = filter_menu_logic(category, max_price, is_available)
    return {"total_found": len(results), "items": results}

# --- Q16: Search Menu ---
@app.get("/menu/search")
def search_menu(keyword: str):
    results = [item for item in menu if keyword.lower() in item["name"].lower() or keyword.lower() in item["category"].lower()]
    if not results:
        return {"message": "No items matched your search."}
    return {"total_found": len(results), "items": results}

# --- Q17: Sort Menu ---
@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by field"}
    if order not in ["asc", "desc"]:
        return {"error": "Invalid order. Use 'asc' or 'desc'"}
    
    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "items": sorted_menu}

# --- Q18: Paginate Menu ---
@app.get("/menu/page")
def paginate_menu(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    sliced_items = menu[start : start + limit]
    total_pages = math.ceil(len(menu) / limit)
    return {"page": page, "limit": limit, "total_items": len(menu), "total_pages": total_pages, "items": sliced_items}

# --- Q20: Browse Menu (Search + Sort + Paginate) ---
@app.get("/menu/browse")
def browse_menu(keyword: Optional[str] = None, sort_by: str = "price", order: str = "asc", page: int = 1, limit: int = 4):
    results = menu
    if keyword:
        results = [item for item in results if keyword.lower() in item["name"].lower() or keyword.lower() in item["category"].lower()]
    results = sorted(results, key=lambda x: x.get(sort_by, x["price"]), reverse=(order == "desc"))
    start = (page - 1) * limit
    sliced_items = results[start : start + limit]
    
    return {
        "metadata": {
            "keyword": keyword, "sort_by": sort_by, "order": order, 
            "page": page, "limit": limit, "total_pages": math.ceil(len(results) / limit)
        },
        "items": sliced_items
    }

# --- Q11: Add Menu Item (CRUD) ---
@app.post("/menu", status_code=status.HTTP_201_CREATED)
def add_menu_item(item: NewMenuItem):
    for existing_item in menu:
        if existing_item["name"].lower() == item.name.lower():
            raise HTTPException(status_code=400, detail="Item with this name already exists")
    
    new_id = max(i["id"] for i in menu) + 1 if menu else 1
    new_item_dict = {"id": new_id, **item.model_dump()}
    menu.append(new_item_dict)
    return new_item_dict

# --- Q3: Get item by ID ---
@app.get("/menu/{item_id}")
def get_item(item_id: int):
    item = find_menu_item(item_id)
    if item:
        return item
    return {"error": "Item not found"}

# --- Q12: Update Menu Item (CRUD) ---
@app.put("/menu/{item_id}")
def update_menu_item(item_id: int, price: Optional[int] = None, is_available: Optional[bool] = None):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if price is not None:
        item["price"] = price
    if is_available is not None:
        item["is_available"] = is_available
    return item

# --- Q13: Delete Menu Item (CRUD) ---
@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    menu.remove(item)
    return {"message": f"Successfully deleted {item['name']}"}

# --- Q14 & Q15: Cart Workflow ---
@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item or not item["is_available"]:
        return {"error": "Item unavailable or not found"}
    
    for cart_item in cart:
        if cart_item["id"] == item_id:
            cart_item["quantity"] += quantity
            return {"message": "Cart updated", "cart": cart}
            
    cart.append({"id": item["id"], "name": item["name"], "price": item["price"], "quantity": quantity})
    return {"message": "Added to cart", "cart": cart}

@app.get("/cart")
def view_cart():
    grand_total = sum(item["price"] * item["quantity"] for item in cart)
    return {"items": cart, "grand_total": grand_total}

@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    global cart
    cart = [item for item in cart if item["id"] != item_id]
    return {"message": "Item removed from cart"}

@app.post("/cart/checkout", status_code=status.HTTP_201_CREATED)
def checkout_cart(details: CheckoutRequest):
    global order_counter
    if not cart:
        return {"error": "Cart is empty"}
        
    placed_orders = []
    for cart_item in cart:
        total_bill = calculate_bill(cart_item["price"], cart_item["quantity"], "delivery")
        new_order = {
            "order_id": order_counter,
            "customer_name": details.customer_name,
            "item_name": cart_item["name"],
            "quantity": cart_item["quantity"],
            "delivery_address": details.delivery_address,
            "total_bill": total_bill,
            "status": "confirmed"
        }
        orders.append(new_order)
        placed_orders.append(new_order)
        order_counter += 1
        
    grand_total = sum(o["total_bill"] for o in placed_orders)
    cart.clear()
    
    return {"message": "Checkout successful", "grand_total": grand_total, "orders": placed_orders}

# --- Q19: Secondary Search & Sort (Orders) ---
@app.get("/orders/search")
def search_orders(customer_name: str):
    matches = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"total_found": len(matches), "orders": matches}

@app.get("/orders/sort")
def sort_orders(sort_by: str = "total_bill", order: str = "asc"):
    sorted_orders = sorted(orders, key=lambda x: x.get(sort_by, 0), reverse=(order == "desc"))
    return {"orders": sorted_orders}

# --- Q4 & Q8: Base Orders Routes ---
@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}

@app.post("/orders")
def place_order(order: OrderRequest):
    global order_counter
    item = find_menu_item(order.item_id)
    if not item or not item["is_available"]:
        return {"error": "Item unavailable"}
        
    total_bill = calculate_bill(item["price"], order.quantity, order.order_type)
    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item_name": item["name"],
        "quantity": order.quantity,
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "total_bill": total_bill,
        "status": "confirmed"
    }
    orders.append(new_order)
    order_counter += 1
    return new_order