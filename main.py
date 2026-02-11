
from fastapi import FastAPI
from fastapi.responses import FileResponse
from models.models import Feedback, User

app = FastAPI()
user = User(name = "Ратасеп Матвей", age = 20, id = 1)
feedbacks = []
@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("./index.html", media_type="text/html")  
    
@app.post("/calculate")
async def calculate(num1: int, num2: int) -> dict:
    result = num1 + num2
    return {"result": result}    
    
    
@app.get("/users")
async def get_users():
    return user
    
@app.post("/user")
async def addUser(user: User) -> dict:
    is_adult = False if user.age < 18 else True
    response_user = {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }
    return response_user
    

@app.post("/feedback")
async def post_feedback(feedback: Feedback) -> dict:
    feedbacks.append(feedback)
    return {"message": f"Спасибо, {feedback.name}! Ваш отзыв успешно отправлен!"}


@app.get("/feedbacks")
async def get_feedbacks():
    return feedbacks

