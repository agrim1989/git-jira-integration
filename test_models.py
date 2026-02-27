import pytest
from models import Base, User, Book, Loan, Fine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_user_model():
    engine = create_engine('postgresql://user:password@localhost/library')
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(username='test', password='test', role='test')
    session.add(user)
    session.commit()
    assert session.query(User).first().username == 'test'

def test_book_model():
    engine = create_engine('postgresql://user:password@localhost/library')
    Session = sessionmaker(bind=engine)
    session = Session()
    book = Book(title='test', author='test')
    session.add(book)
    session.commit()
    assert session.query(Book).first().title == 'test'

def test_loan_model():
    engine = create_engine('postgresql://user:password@localhost/library')
    Session = sessionmaker(bind=engine)
    session = Session()
    loan = Loan(user_id=1, book_id=1)
    session.add(loan)
    session.commit()
    assert session.query(Loan).first().user_id == 1

def test_fine_model():
    engine = create_engine('postgresql://user:password@localhost/library')
    Session = sessionmaker(bind=engine)
    session = Session()
    fine = Fine(loan_id=1, amount=10)
    session.add(fine)
    session.commit()
    assert session.query(Fine).first().loan_id == 1