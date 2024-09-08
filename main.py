from _datetime import datetime
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
import motor.motor_asyncio
from bson import ObjectId
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator
import shutil
from typing_extensions import Annotated
from fastapi.staticfiles import StaticFiles


client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://parabellum:bluu12345@cluster0.5kumd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

db = client.LMS

student_collection = db.students
book_collection = db.books
user_collection = db.user
borrowing_collection = db.borrowing
request_collection = db.request

PyObjectId = Annotated[str, BeforeValidator(str)]

tags_metadata = [
    {
        "name": "Students",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "Books",
        "description": "Manage items. So _fancy_ they have their own docs.",
    },
{
        "name": "Users",
        "description": "Manage items. So _fancy_ they have their own docs.",
    },
{
        "name": "Borrowing",
        "description": "Manage items. So _fancy_ they have their own docs.",
    },
{
        "name": "Borrow Request",
        "description": "Manage items. So _fancy_ they have their own docs.",
    },
]

UPLOAD_DIRECTORY = "./uploaded_books_images"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

class Student(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)

class Book(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(...)
    author: str = Field(...)
    isbn: str = Field(...)
    category: str = Field(...)
    image_url: Optional[str] = None

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)

class Borrowing(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: str = Field(...)
    user_id: str = Field(...)
    borrow_date: datetime = Field(...)
    return_date: datetime = Field(...)
    returned: bool = Field(False)

class BorrowRequest(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: str = Field(...)
    user_id: str = Field(...)

app = FastAPI()

# Mount the directory to serve static files
app.mount("/uploaded_books_images", StaticFiles(directory="uploaded_books_images"), name="uploaded_books_images")

# Manage Students
@app.get("/students", tags=["Students"])
async def get_Students():
    mapArr = []
    all_students = student_collection.find({})

    async for student in all_students:
        mapArr.append(Student(**student))

    return mapArr

@app.post("/students", tags=["Students"])
async def add_Student(student:Student):
    addStudent = await student_collection.insert_one(student.dict())
    result = await student_collection.find_one({"_id":addStudent.inserted_id})

    result["_id"] = str(result["_id"])

    return result

@app.get("/students/{id}" , tags=["Students"])
async def getStudentById(id:str):
    student = await student_collection.find_one({"_id": ObjectId(id)})

    student["_id"] = str(student["_id"])

    return student

@app.put("/students/{id}", tags=["Students"])
async def editStudent(id:str, student: Student):
    student = await student_collection.find_one_and_update({"_id": ObjectId(id)},
            {"$set": student.dict()},
            return_document=True)
    student["_id"] = str(student["_id"])

    return student

@app.delete("/students/{id}", tags=["Students"])
async def deleteStudent(id:str):
    await student_collection.delete_one({"_id": ObjectId(id)})
    students = []
    getStudents = student_collection.find({})

    async for student in getStudents:
        students.append(Student(**student))

    return students

# Manage Books
@app.get("/books", tags=["Books"])
async def get_Books():
    mapArr = []
    all_books = book_collection.find({})

    async for book in all_books:
        mapArr.append(Book(**book))

    return mapArr

# Important for future projects that involve uploading images!!!!!!!!!!!
@app.post("/books", tags=["Books"])
async def add_Book(
        title: str = Form(...),
        author: str = Form(...),
        isbn: str = Form(...),
        category: str = Form(...),
        image: UploadFile = File(None)
):
    book = Book(title=title, author=author, isbn=isbn, category=category)

    if image:
        # Save the uploaded image file
        file_location = f"{UPLOAD_DIRECTORY}/{image.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Generate the image URL, make sure it matches the static route
        image_url = f"https://library-management-system-ntef-g2qpm38xg.vercel.app/uploaded_books_images/{image.filename}"
        book.image_url = image_url  # Assign image URL to the book

    # Insert the book into MongoDB
    addBook = await book_collection.insert_one(book.dict())
    result = await book_collection.find_one({"_id": addBook.inserted_id})
    result["_id"] = str(result["_id"])

    return result


@app.get("/books/{id}" , tags=["Books"])
async def getBookById(id:str):
    book = await book_collection.find_one({"_id": ObjectId(id)})

    book["_id"] = str(book["_id"])

    return book

@app.put("/books/{id}", tags=["Books"])
async def editBook(id:str, book: Book):
    booky = await book_collection.find_one_and_update({"_id": ObjectId(id)},
            {"$set": book.dict()},
            return_document=True)
    booky["_id"] = str(booky["_id"])

    return booky

@app.delete("/books/{id}", tags=["Books"])
async def deleteBook(id:str):
    await book_collection.delete_one({"_id": ObjectId(id)})
    books = []
    getBooks = book_collection.find({})

    async for book in getBooks:
        books.append(Book(**book))

    return books

# User Endpoint

@app.get("/users", tags=["Users"])
async def get_all_users():
    all_Users = user_collection.find({})

    user_Arr = []

    async for user in all_Users:
        user_Arr.append(User(**user))

    return user_Arr

@app.post("/users", tags=["Users"])
async def add_user(user:User):
    addUser = await user_collection.insert_one(user.dict())
    result = await user_collection.find_one({"_id": addUser.inserted_id})

    result["_id"] = str(result["_id"])
    return result


@app.get("/users/login", tags=["Users"])
async def Login_User(email: str, password: str):
    try:
        # Find user by email and password
        query_User = await user_collection.find_one({"email": email, "password": password})

        # Check if the user exists
        if query_User:
            # Convert ObjectId to string for JSON serialization
            query_User["_id"] = str(query_User["_id"])
            return query_User
        else:
            # Raise an HTTP 404 error if the user is not found
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        # Log and raise an HTTP 500 error with the exception message
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/users/{id}", tags=["Users"])
async def get_User_By_Id(id:str):
    getUser = await user_collection.find_one({"_id": ObjectId(id)})

    getUser["_id"] = str(getUser["_id"])

    return getUser


@app.put("/users/{id}", tags=["Users"])
async def Edit_User_Data(id: str, user_update: User):
    # Fetch the existing user data
    existing_user = await user_collection.find_one({"_id": ObjectId(id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare the update data
    update_data = user_update.dict(exclude_unset=True)

    # Update only the fields provided
    if update_data:
        updated_user = await user_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": update_data},
            return_document=True
        )

        if updated_user:
            updated_user["_id"] = str(updated_user["_id"])
            return updated_user
        else:
            raise HTTPException(status_code=500, detail="Update failed")
    else:
        return {"message": "No fields provided for update"}


@app.delete("/users/{id}", tags=["Users"])
async def Delete_User(id:str):
    await user_collection.delete_one({"_id": ObjectId(id)})
    users = []
    getUsers = user_collection.find({})

    async for user in getUsers:
        users.append(User(**user))

    return users

# Borrowing

@app.get("/borrowing", tags=["Borrowings"])
async def Get_All_Borrowings():
    allBorrowings = borrowing_collection.find({})

    borrowings = []

    async for borrows in allBorrowings:
        borrowings.append(Borrowing(**borrows))

    return borrowings

@app.post("/borrowing",tags=["Borrowings"])
async def Add_Borrowing(body:Borrowing):
    addToDB = await borrowing_collection.insert_one(body.dict())

    viewAdded = await borrowing_collection.find_one({"_id": ObjectId(addToDB.inserted_id)})

    viewAdded["_id"] = str(viewAdded["_id"])

    return viewAdded

@app.get("/borrowing/{id}", tags=["Borrowings"])
async def Get_Borrowing_By_Id(id:str):
    getBorrowing = await borrowing_collection.find_one({"_id": ObjectId(id)})

    getBorrowing["_id"] = str(getBorrowing["_id"])

    return getBorrowing

@app.put("/borrowing/{id}", tags=["Borrowings"])
async def Update_Borrowing(id:str, body:Borrowing):
    updateItem = await borrowing_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": body.dict()},
            return_document=True
        )

    updateItem["_id"] = str(updateItem["_id"])

    return updateItem

@app.delete("/borrowing/{id}", tags=["Borrowings"])
async def Delete_Borrowing(id:str):
    await borrowing_collection.delete_one({"_id": ObjectId(id)})

    getAllItems = borrowing_collection.find({})

    allItems = []

    async for item in getAllItems:
        allItems.append(Borrowing(**item))

    return allItems

# Requests

@app.get("/requests", tags=["Requests"])
async def Get_All_Requests():
    getRequests = request_collection.find({})
    requests = []

    async for request in getRequests:
        requests.append(BorrowRequest(**request))

    return requests

@app.post("/requests", tags=["Requests"])
async def Create_Request(body:BorrowRequest):
    createRequest = await request_collection.insert_one(body.dict())
    getAddedReq = await request_collection.find_one({"_id": ObjectId(createRequest.inserted_id)})

    getAddedReq["_id"] = str(getAddedReq["_id"])

    return getAddedReq



@app.get("/")
async def main ():
    return {"welcome to Ahuekwe Prince Ugochukwu first fastAPI Project"}