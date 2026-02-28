from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI(title="Library Management System API")

# Mock Database
books = {}  # id -> book dict
members = {} # id -> member dict
borrowed = {} # book_id -> dict of member_id -> due_date

class Book(BaseModel):
    id: str
    title: str
    author: str
    total_copies: int
    available_copies: int

class Member(BaseModel):
    id: str
    name: str

class BorrowBookRequest(BaseModel):
    member_id: str

@app.post("/books", response_model=Book)
def add_book(book: Book):
    if book.id in books:
        raise HTTPException(status_code=400, detail="Book already exists")
    books[book.id] = book.dict()
    return book

@app.post("/members", response_model=Member)
def add_member(member: Member):
    if member.id in members:
        raise HTTPException(status_code=400, detail="Member already exists")
    members[member.id] = member.dict()
    return member

@app.post("/books/{book_id}/borrow")
def borrow_book(book_id: str, request: BorrowBookRequest):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    if request.member_id not in members:
        raise HTTPException(status_code=404, detail="Member not found")
        
    book = books[book_id]
    if book["available_copies"] <= 0:
        raise HTTPException(status_code=400, detail="No copies available")
        
    book["available_copies"] -= 1
    due_date = datetime.now() + timedelta(days=14)
    if book_id not in borrowed:
        borrowed[book_id] = {}
        
    borrowed[book_id][request.member_id] = due_date.isoformat()
    return {"status": "success", "due_date": due_date.isoformat()}

@app.post("/books/{book_id}/return")
def return_book(book_id: str, request: BorrowBookRequest):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book_id not in borrowed or request.member_id not in borrowed[book_id]:
        raise HTTPException(status_code=400, detail="Book not borrowed by this member")
        
    del borrowed[book_id][request.member_id]
    books[book_id]["available_copies"] += 1
    return {"status": "success"}
    
@app.get("/books", response_model=List[Book])
def list_books():
    return list(books.values())
