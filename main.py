from _datetime import datetime
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
import motor.motor_asyncio
from bson import ObjectId
from typing import Optional, List
from pydantic.functional_validators import BeforeValidator
import shutil
from typing_extensions import Annotated
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure your Cloudinary credentials
cloudinary.config(
    cloud_name="dejeplzpv",
    api_key="124721334338285",
    api_secret="CTYwG9PTDXhWGS-1L2XWhzeqjNU"
)


client = MongoClient('mongodb+srv://parabellum:bluu12345@cluster0.5kumd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

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

class OptionalStudent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class Book(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(...)
    author: str = Field(...)
    isbn: str = Field(...)
    category: str = Field(...)
    image_url: Optional[str] = None

class OptionalBook(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)

class OptionalUser(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class Borrowing(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: str = Field(...)
    user_id: str = Field(...)
    borrow_date: datetime = Field(...)
    return_date: datetime = Field(...)
    returned: bool = Field(False)

class OptionalBorrowing(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: Optional[str] = None
    user_id: Optional[str] = None
    borrow_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    returned: Optional[bool] = None

class BorrowRequest(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: str = Field(...)
    user_id: str = Field(...)

class OptionalBorrowRequest(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    book_id: Optional[str] = None
    user_id: Optional[str] = None

app = FastAPI()

# Mount the directory to serve static files
app.mount("/uploaded_books_images", StaticFiles(directory="uploaded_books_images"), name="uploaded_books_images")

# Manage Students
@app.get("/students", tags=["Students"])
def get_Students():
    mapArr = []
    all_students = student_collection.find({})

    for student in all_students:
        mapArr.append(Student(**student))

    return mapArr

@app.post("/students", tags=["Students"])
def add_Student(student:Student):
    addStudent = student_collection.insert_one(student.dict())
    result = student_collection.find_one({"_id":addStudent.inserted_id})

    result["_id"] = str(result["_id"])

    return result

@app.get("/students/{id}" , tags=["Students"])
def getStudentById(id:str):
    student = student_collection.find_one({"_id": ObjectId(id)})

    student["_id"] = str(student["_id"])

    return student

@app.put("/students/{id}", tags=["Students"])
def editStudent(id:str, student: Student):
    student = student_collection.find_one_and_update({"_id": ObjectId(id)},
            {"$set": student.dict()},
            return_document=True)
    student["_id"] = str(student["_id"])

    return student


@app.patch("/students/{id}", tags=["Students"])
def Update_Student(id: str, body: OptionalStudent):
    update_data = {k: v for k, v in body.dict().items() if v is not None}

    # Update the student record
    student_update = student_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})

    # Fetch the updated student document from the correct collection
    updated_student = student_collection.find_one({"_id": ObjectId(id)})

    if updated_student:
        updated_student["_id"] = str(updated_student["_id"])  # Convert ObjectId to string
        return updated_student
    else:
        raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/students/{id}", tags=["Students"])
def deleteStudent(id:str):
    student_collection.delete_one({"_id": ObjectId(id)})
    students = []
    getStudents = student_collection.find({})

    for student in getStudents:
        students.append(Student(**student))

    return students

# Manage Books
@app.get("/books", tags=["Books"])
def get_Books():
    mapArr = []
    all_books = book_collection.find({})

    for book in all_books:
        mapArr.append(Book(**book))

    return mapArr

# Important for future projects that involve uploading images!!!!!!!!!!!
@app.post("/books", tags=["Books"])
def add_Book(
request: Request,
        title: str = Form(...),
        author: str = Form(...),
        isbn: str = Form(...),
        category: str = Form(...),
        image: UploadFile = File(None),
):
    book = Book(title=title, author=author, isbn=isbn, category=category)

    if image:
        try:
            # Upload the image to Cloudinary
            upload_result = cloudinary.uploader.upload(image.file, folder="books")

            # Store the URL of the uploaded image
            book.image_url = upload_result.get("url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # Insert the book into MongoDB
    addBook = book_collection.insert_one(book.dict())
    result = book_collection.find_one({"_id": addBook.inserted_id})
    result["_id"] = str(result["_id"])

    return result

@app.get("/books/{id}" , tags=["Books"])
def getBookById(id:str):
    book = book_collection.find_one({"_id": ObjectId(id)})

    book["_id"] = str(book["_id"])

    return book

@app.put("/books/{id}", tags=["Books"])
def editBook(id:str, book: OptionalBook):
    booky = book_collection.find_one_and_update({"_id": ObjectId(id)},
            {"$set": book.dict()},
            return_document=True)
    booky["_id"] = str(booky["_id"])

    return booky

@app.delete("/books/{id}", tags=["Books"])
def deleteBook(id:str):
    book_collection.delete_one({"_id": ObjectId(id)})
    books = []
    getBooks = book_collection.find({})

    for book in getBooks:
        books.append(Book(**book))

    return books

# User Endpoint

@app.get("/users", tags=["Users"])
def get_all_users():
    all_Users = user_collection.find({})

    user_Arr = []

    for user in all_Users:
        user_Arr.append(User(**user))

    return user_Arr

@app.post("/users", tags=["Users"])
def add_user(user:User):
    addUser = user_collection.insert_one(user.dict())
    result = user_collection.find_one({"_id": addUser.inserted_id})

    result["_id"] = str(result["_id"])
    return result


@app.get("/users/login", tags=["Users"])
def Login_User(email: str, password: str):
    try:
        # Find user by email and password
        query_User = user_collection.find_one({"email": email, "password": password})

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
def get_User_By_Id(id:str):
    getUser = user_collection.find_one({"_id": ObjectId(id)})

    getUser["_id"] = str(getUser["_id"])

    return getUser


@app.put("/users/{id}", tags=["Users"])
def Edit_User_Data(id: str, user_update: OptionalUser):
    # Fetch the existing user data
    existing_user = user_collection.find_one({"_id": ObjectId(id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare the update data
    update_data = user_update.dict(exclude_unset=True)

    # Update only the fields provided
    if update_data:
        updated_user = user_collection.find_one_and_update(
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
def Delete_User(id:str):
    user_collection.delete_one({"_id": ObjectId(id)})
    users = []
    getUsers = user_collection.find({})

    for user in getUsers:
        users.append(User(**user))

    return users

# Borrowing

@app.get("/borrowing", tags=["Borrowings"])
def Get_All_Borrowings():
    allBorrowings = borrowing_collection.find({})

    borrowings = []

    for borrows in allBorrowings:
        borrowings.append(Borrowing(**borrows))

    return borrowings

@app.post("/borrowing",tags=["Borrowings"])
def Add_Borrowing(body:Borrowing):
    addToDB = borrowing_collection.insert_one(body.dict())

    viewAdded = borrowing_collection.find_one({"_id": ObjectId(addToDB.inserted_id)})

    viewAdded["_id"] = str(viewAdded["_id"])

    return viewAdded

@app.get("/borrowing/{id}", tags=["Borrowings"])
def Get_Borrowing_By_Id(id:str):
    getBorrowing = borrowing_collection.find_one({"_id": ObjectId(id)})

    getBorrowing["_id"] = str(getBorrowing["_id"])

    return getBorrowing

@app.put("/borrowing/{id}", tags=["Borrowings"])
def Update_Borrowing(id:str, body:OptionalBorrowing):
    updateItem = borrowing_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": body.dict()},
            return_document=True
        )

    updateItem["_id"] = str(updateItem["_id"])

    return updateItem

@app.delete("/borrowing/{id}", tags=["Borrowings"])
def Delete_Borrowing(id:str):
    borrowing_collection.delete_one({"_id": ObjectId(id)})

    getAllItems = borrowing_collection.find({})

    allItems = []

    for item in getAllItems:
        allItems.append(Borrowing(**item))

    return allItems

# Requests

@app.get("/requests", tags=["Requests"])
def Get_All_Requests():
    getRequests = request_collection.find({})
    requests = []

    for request in getRequests:
        requests.append(BorrowRequest(**request))

    return requests

@app.post("/requests", tags=["Requests"])
def Create_Request(body:BorrowRequest):
    createRequest = request_collection.insert_one(body.dict())
    getAddedReq = request_collection.find_one({"_id": ObjectId(createRequest.inserted_id)})

    getAddedReq["_id"] = str(getAddedReq["_id"])

    return getAddedReq

@app.get("/requests/{id}", tags=["Requests"])
def Find_Request_By_Id (id:str):
    req = request_collection.find_one({"_id": ObjectId(id)})

    req["_id"] = str(req["_id"])
    return req

@app.put("/request/{id}", tags=["Requests"])
def Edit_Request(id:str, body:OptionalBorrowRequest):
    editQuery = request_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": body.dict()},
        return_document= True
    )

    # getEditedItem = request_collection.find_one({"_id": ObjectId(editQuery.inserted_id)})

    editQuery["_id"] = str(editQuery["_id"])

    return editQuery


@app.patch("/request/{id}", tags=["Requests"])
def Patch_Request(id: str, body: OptionalBorrowRequest):
    try:
        # Check if the id is a valid ObjectId
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    # Create a dictionary of only the fields that have been provided for update
    update_data = {k: v for k, v in body.dict().items() if v is not None}

    # If no data is provided to update
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # Perform the update
    result = request_collection.update_one({"_id": oid}, {"$set": update_data})

    # If no documents were matched, return a 404 error
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")

    # Fetch the updated document
    updated_request = request_collection.find_one({"_id": oid})

    if updated_request:
        updated_request["_id"] = str(updated_request["_id"])  # Convert ObjectId to string
        return updated_request
    else:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated request")


@app.get("/")
def main ():
    return {"welcome to Ahuekwe Prince Ugochukwu first fastAPI Project"}