"""
databasemanager.py
Handles PostgreSQL connections and CRUD operations.
FINAL VERSION: Includes CRUD for Books and Authors.
"""
import psycopg2
from psycopg2 import sql
import datetime

# CONFIGURATION
# !! IMPORTANT: Update these credentials to match your PostgreSQL setup !!
DB_HOST = "localhost"
DB_NAME = "smart_library"
DB_USER = "postgres"
DB_PASS = "SHERIFF37"
DB_PORT = "5432"

class DatabaseManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT
            )
            self.conn.autocommit = True
            print("Database connected successfully.")
        except Exception as e:
            print(
                f"Error connecting to database. Please check credentials and ensure the DB 'smart_library' is running: {e}")
            self.conn = None

    def authenticate_user(self, username, password):
        """Checks credentials and returns user details."""
        if not self.conn: return None
        # Note: In a real app, password_hash should be properly checked (e.g., bcrypt)
        query = "SELECT id, username, full_name, email, role_id FROM Users WHERE username=%s AND password_hash=%s"
        with self.conn.cursor() as cur:
            cur.execute(query, (username, password))
            row = cur.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "full_name": row[2], "email": row[3], "role_id": row[4]}
            return None

    # --- BOOK CATALOG & LOANS ---

    def get_all_books(self, search_query=None):
        """Retrieves all books with their authors, optionally filtering."""
        base_query = """
            SELECT b.id, b.title, b.genre, b.publication_year, b.available, 
                   COALESCE(string_agg(a.name, ', '), 'N/A') as authors
            FROM Books b 
            LEFT JOIN BookAuthors ba ON b.id = ba.book_id
            LEFT JOIN Authors a ON ba.author_id = a.id
        """
        params = []
        if search_query:
            base_query += """
                WHERE b.title ILIKE %s OR b.genre ILIKE %s OR a.name ILIKE %s
            """
            term = f"%{search_query}%"
            params = [term, term, term]

        base_query += " GROUP BY b.id, b.title, b.genre, b.publication_year, b.available ORDER BY b.id"

        with self.conn.cursor() as cur:
            cur.execute(base_query, tuple(params))
            return cur.fetchall()

    def borrow_book(self, user_id, book_id):
        """Attempts to borrow a book. Relies on SQL Triggers for logic (max 3 loans, update availability)."""
        try:
            with self.conn.cursor() as cur:
                due_date = datetime.date.today() + datetime.timedelta(days=7)
                query = "INSERT INTO Loans (book_id, user_id, borrow_date, due_date) VALUES (%s, %s, CURRENT_DATE, %s)"
                cur.execute(query, (book_id, user_id, due_date))
                return True, "Book borrowed successfully!"
        except psycopg2.Error as e:
            return False, str(e).split('\n')[0]

    def return_book(self, loan_id):
        """Returns a book by updating the return_date. Relies on SQL Trigger to update availability."""
        try:
            with self.conn.cursor() as cur:
                query = "UPDATE Loans SET return_date = CURRENT_DATE WHERE id = %s"
                cur.execute(query, (loan_id,))
                return True, "Book returned successfully."
        except Exception as e:
            return False, str(e)

    def get_user_loans(self, user_id):
        query = """
            SELECT l.id, b.title, l.borrow_date, l.due_date, l.return_date 
            FROM Loans l JOIN Books b ON l.book_id = b.id
            WHERE l.user_id = %s AND l.return_date IS NULL
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()

    # --- LIBRARIAN: BOOK CRUD ---
    def add_book(self, title, genre, year, author_ids):
        """Adds a new book and links it to authors."""
        try:
            with self.conn.cursor() as cur:
                # 1. Insert Book
                book_query = "INSERT INTO Books (title, genre, publication_year) VALUES (%s, %s, %s) RETURNING id"
                cur.execute(book_query, (title, genre, year))
                book_id = cur.fetchone()[0]

                # 2. Link Authors
                for author_id in author_ids:
                    link_query = "INSERT INTO BookAuthors (book_id, author_id) VALUES (%s, %s)"
                    cur.execute(link_query, (book_id, author_id))

                return True, f"Book '{title}' added successfully with ID {book_id}."
        except Exception as e:
            return False, str(e)

    def update_book(self, book_id, title, genre, year, author_ids):
        """Updates book details and replaces author links."""
        try:
            with self.conn.cursor() as cur:
                # 1. Update Book Details
                update_query = "UPDATE Books SET title=%s, genre=%s, publication_year=%s WHERE id=%s"
                cur.execute(update_query, (title, genre, year, book_id))

                # 2. Clear existing Author Links
                cur.execute("DELETE FROM BookAuthors WHERE book_id=%s", (book_id,))

                # 3. Insert new Author Links
                for author_id in author_ids:
                    link_query = "INSERT INTO BookAuthors (book_id, author_id) VALUES (%s, %s)"
                    cur.execute(link_query, (book_id, author_id))

                return True, f"Book ID {book_id} updated successfully."
        except Exception as e:
            return False, str(e)

    def delete_book(self, book_id):
        """Deletes a book. Cascades to BookAuthors. Will fail if active loans exist (RESTRICT)."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM Books WHERE id=%s", (book_id,))
                return True, f"Book ID {book_id} deleted successfully."
        except psycopg2.Error as e:
            # Check for foreign key violation (active loans)
            if 'violates foreign key constraint "fk_book"' in str(e):
                return False, "Cannot delete book. There are active loans associated with it."
            return False, str(e)

    # --- LIBRARIAN: AUTHOR CRUD ---
    def get_all_authors(self):
        """Retrieves all authors."""
        query = "SELECT id, name, bio FROM Authors ORDER BY name"
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def add_author(self, name, bio):
        """Adds a new author."""
        try:
            with self.conn.cursor() as cur:
                query = "INSERT INTO Authors (name, bio) VALUES (%s, %s)"
                cur.execute(query, (name, bio))
                return True, f"Author '{name}' added successfully."
        except psycopg2.Error as e:
            if 'duplicate key value violates unique constraint' in str(e):
                return False, f"Author name '{name}' already exists."
            return False, str(e)

    def delete_author(self, author_id):
        """Deletes an author. Cascades to BookAuthors links."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM Authors WHERE id=%s", (author_id,))
                return True, "Author deleted successfully."
        except psycopg2.Error as e:
            # Although BookAuthors CASCADE, if the author table had other constraints, this would catch it.
            return False, str(e)

    # --- DASHBOARD & CLUB METHODS (Existing) ---
    def get_dashboard_stats(self):
        stats = {}
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM Books")
            stats['books'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Users WHERE role_id = 2")
            stats['members'] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Loans WHERE return_date IS NULL")
            stats['active_loans'] = cur.fetchone()[0]
        return stats

    def get_popular_books(self):
        query = "SELECT * FROM PopularBooksReport LIMIT 10"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except:
            return []

    def get_overdue_books(self):
        query = "SELECT * FROM OverdueBooksReport"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except:
            return []

    def get_all_clubs(self):
        query = """
            SELECT c.id, c.name, c.description, u.full_name as creator 
            FROM BookClubs c 
            JOIN Users u ON c.created_by = u.id
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def join_club(self, user_id, club_id):
        try:
            with self.conn.cursor() as cur:
                query = "INSERT INTO ClubMemberships (club_id, user_id) VALUES (%s, %s)"
                cur.execute(query, (club_id, user_id))
                return True, "Joined club successfully!"
        except psycopg2.Error:
            return False, "You are already a member of this club."

    def create_club(self, name, description, user_id):
        try:
            with self.conn.cursor() as cur:
                query = "INSERT INTO BookClubs (name, description, created_by) VALUES (%s, %s, %s)"
                cur.execute(query, (name, description, user_id))
                return True, "Club created successfully!"
        except psycopg2.Error as e:
            return False, f"Error: {e}"

    def get_club_members(self, club_id):
        query = """
            SELECT u.full_name, u.email, cm.join_date 
            FROM ClubMemberships cm 
            JOIN Users u ON cm.user_id = u.id 
            WHERE cm.club_id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (club_id,))
            return cur.fetchall()