from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from models.response import ErrorResponse
from models.user import UserProfile

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


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    
    for error in exc.errors():
        
        field_name = " -> ".join([str(loc) for loc in error["loc"][1:]]) 
        error_msg = error["msg"]
        formatted_errors.append({
            "field": field_name,
            "error": error_msg
        })

    
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_FAILED",
            "message": "Введенные данные не прошли проверку. Пожалуйста, исправьте ошибки.",
            "details": formatted_errors
        }
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
        
    product["stock"] -= amount
    return {"message": "Покупка успешна", "remaining_stock": product["stock"]}

# 1. Конечная точка, принимающая JSON нагрузку
@app.post("/profiles")
def create_profile(profile: UserProfile):

    return {
        "message": "Пользовательский профиль успешно создан!",
        "profile": profile
    }


