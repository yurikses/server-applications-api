from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models.response import ErrorResponse

class ItemNotFoundException(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        self.message = f"Товар с ID {item_id} не найден."
        self.status_code = 404

class InsufficientStockException(Exception):
    def __init__(self, item_name: str, requested: int, available: int):
        self.message = f"Недостаточно товара '{item_name}' на складе. Запрошено: {requested}, Доступно: {available}."
        self.status_code = 400


MOCK_PRODUCTS = {
    1: {"name": "Ноутбук", "stock": 5},
    2: {"name": "Мышка", "stock": 50},
}

app = FastAPI()

@app.exception_handler(ItemNotFoundException)
async def item_not_found_handler(request: Request, exc: ItemNotFoundException):
   
    error_response = ErrorResponse(
        error_code="ITEM_NOT_FOUND",
        message=exc.message,
        details={"requested_id": exc.item_id}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

@app.exception_handler(InsufficientStockException)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockException):
    error_response = ErrorResponse(
        error_code="INSUFFICIENT_STOCK",
        message=exc.message
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


@app.get("/products/{product_id}", responses={404: {"model": ErrorResponse}})
def get_product(product_id: int):
    
    if product_id not in MOCK_PRODUCTS:
        raise ItemNotFoundException(item_id=product_id)
        
    return MOCK_PRODUCTS[product_id]


@app.post("/products/{product_id}/buy", responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def buy_product(product_id: int, amount: int):
   
    if product_id not in MOCK_PRODUCTS:
        raise ItemNotFoundException(item_id=product_id)
        
    product = MOCK_PRODUCTS[product_id]
    
   
    if amount > product["stock"]:
        raise InsufficientStockException(
            item_name=product["name"], 
            requested=amount, 
            available=product["stock"]
        )
        
    # Успешная покупка
    product["stock"] -= amount
    return {"message": "Покупка успешна", "remaining_stock": product["stock"]}



