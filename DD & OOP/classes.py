class User:
    """Base class for all system users."""

    def __init__(self, user_id, username, full_name, email, role_id):
        self._id = user_id
        self._username = username
        self.full_name = full_name
        self.email = email
        self.role_id = role_id

    @property
    def id(self):
        return self._id

    @property
    def username(self):
        return self._username


class Librarian(User):
    """Inherits from User. Can manage books and clubs."""

    def __init__(self, user_id, username, full_name, email):
        super().__init__(user_id, username, full_name, email, role_id=1)


class Member(User):
    """Inherits from User. Can borrow books and join clubs."""

    def __init__(self, user_id, username, full_name, email):
        super().__init__(user_id, username, full_name, email, role_id=2)


class Book:
    """Represents a book entity."""

    def __init__(self, book_id, title, genre, year, available):
        self._id = book_id
        self.title = title
        self.genre = genre
        self.year = year
        self._available = available

    @property
    def available(self):
        return self._available

    @property
    def id(self):
        return self._id


class Loan:
    """Represents a loan transaction."""

    def __init__(self, loan_id, book_title, borrow_date, due_date, return_date):
        self.loan_id = loan_id
        self.book_title = book_title
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.return_date = return_date

    @property
    def status(self):
        if self.return_date:
            return "Returned"
        return "Active"