"""
application.py
FINAL STYLED VERSION: Integrates all functionality with the custom blue/white theme (QSS).
Includes Login, Dashboard (styled stats), Book Catalog (Search/CRUD), Loans, and Book Clubs.
"""
import sys
import datetime
from PyQt5.QtGui import QPainter, QFont, QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                             QTabWidget, QHeaderView, QGroupBox, QFormLayout, QDialog, QDialogButtonBox,
                             QListWidget, QListWidgetItem, QTextEdit, QSpinBox, QSpacerItem, QSizePolicy)

# Import your custom classes and database manager
from classes import User, Librarian, Member
from databasemanager import DatabaseManager

# Beautiful Blue-White-Black Theme (Custom QSS)
STYLE = """
    QMainWindow, QDialog {
        background-color: #0d1b2a;
    }
    QLabel {
        color: #e0e1dd;
        font-size: 14px;
    }
    /* Style for the main stat boxes */
    QGroupBox {
        border: 2px solid #415a77;
        border-radius: 10px;
        margin-top: 15px;
        background-color: #1b263b;
        color: #e0e1dd;
        padding: 10px;
        font-size: 16px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 3px;
    }
    QLineEdit, QSpinBox, QTextEdit {
        background-color: #1b263b;
        color: #e0e1dd;
        border: 2px solid #415a77;
        border-radius: 10px;
        padding: 10px;
        font-size: 14px;
    }
    QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
        border: 2px solid #778da9;
    }
    QPushButton {
        background-color: #415a77;
        color: #e0e1dd;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #778da9;
    }
    QTabWidget::pane { 
        border: 0; 
    }
    QTabBar::tab {
        background: #415a77;
        color: #e0e1dd;
        padding: 10px 20px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #778da9;
        color: #0d1b2a;
        font-weight: bold;
    }
    QTableWidget {
        background-color: #1b263b;
        color: #e0e1dd;
        gridline-color: #415a77;
        border: 1px solid #415a77;
        selection-background-color: #415a77;
    }
    QHeaderView::section {
        background-color: #415a77;
        color: #e0e1dd;
        padding: 8px;
        border: 1px solid #0d1b2a;
        font-weight: bold;
    }
    QListWidget {
        background-color: #1b263b;
        color: #e0e1dd;
        border: 1px solid #415a77;
    }
    QListWidget::item:selected {
        background-color: #778da9;
        color: #0d1b2a;
    }
"""


# --- DIALOGS FOR MANAGEMENT ---

class AuthorManagementDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Manage Authors")
        self.setGeometry(300, 300, 450, 400)

        layout = QVBoxLayout(self)

        # 1. Author List
        self.author_list = QTableWidget()
        self.author_list.setColumnCount(3)
        self.author_list.setHorizontalHeaderLabels(['ID', 'Name', 'Bio'])
        self.author_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.author_list)

        # 2. Add/Delete Controls
        control_group = QGroupBox("Add/Delete")
        control_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.bio_input = QLineEdit()
        control_layout.addRow("Name:", self.name_input)
        control_layout.addRow("Bio:", self.bio_input)

        btn_add = QPushButton("Add Author")
        btn_add.clicked.connect(self.add_author)

        btn_delete = QPushButton("Delete Selected")
        btn_delete.clicked.connect(self.delete_author)

        h_layout = QHBoxLayout()
        h_layout.addWidget(btn_add)
        h_layout.addWidget(btn_delete)

        control_layout.addRow(h_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        self.load_authors()

    def load_authors(self):
        authors = self.db.get_all_authors()
        self.author_list.setRowCount(0)
        for row_idx, author_data in enumerate(authors):
            self.author_list.insertRow(row_idx)
            for col_idx, data in enumerate(author_data):
                self.author_list.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def add_author(self):
        name = self.name_input.text().strip()
        bio = self.bio_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Author name cannot be empty.")
            return

        success, msg = self.db.add_author(name, bio)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.name_input.clear()
            self.bio_input.clear()
            self.load_authors()
        else:
            QMessageBox.warning(self, "Error", msg)

    def delete_author(self):
        row = self.author_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Author", "Please select an author to delete.")
            return

        author_id = self.author_list.item(row, 0).text()

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     "Are you sure you want to delete this author? This will unlink them from all books.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_author(author_id)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.load_authors()
            else:
                QMessageBox.warning(self, "Error", msg)


class BookManagementDialog(QDialog):
    def __init__(self, db_manager, book_data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.book_data = book_data

        self.setWindowTitle("Manage Book" if book_data else "Add New Book")
        self.setGeometry(300, 300, 500, 450)

        self.all_authors = self.db.get_all_authors()

        layout = QVBoxLayout(self)

        # Form Fields
        form = QFormLayout()
        self.title_input = QLineEdit()
        self.genre_input = QLineEdit()
        self.year_input = QSpinBox()
        self.year_input.setRange(1800, datetime.date.today().year)
        self.year_input.setValue(datetime.date.today().year)

        form.addRow("Title:", self.title_input)
        form.addRow("Genre:", self.genre_input)
        form.addRow("Pub. Year:", self.year_input)
        layout.addLayout(form)

        # Author Selection
        author_group = QGroupBox("Select Authors")
        author_layout = QVBoxLayout()
        self.author_list_widget = QListWidget()
        self.author_list_widget.setSelectionMode(QListWidget.MultiSelection)

        for author in self.all_authors:
            author_id, name, _ = author
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, author_id)
            self.author_list_widget.addItem(item)

        author_layout.addWidget(self.author_list_widget)
        author_group.setLayout(author_layout)
        layout.addWidget(author_group)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_book)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if self.book_data:
            self.load_data()

    def load_data(self):
        # Data structure: ID, Title, Genre, Year, Available, Authors_Str
        _, title, genre, year, _, authors_str = self.book_data

        self.title_input.setText(title)
        self.genre_input.setText(genre)
        self.year_input.setValue(year)

        current_authors = [name.strip() for name in authors_str.split(',')]
        for i in range(self.author_list_widget.count()):
            item = self.author_list_widget.item(i)
            if item.text() in current_authors:
                item.setSelected(True)

    def save_book(self):
        title = self.title_input.text().strip()
        genre = self.genre_input.text().strip()
        year = self.year_input.value()

        selected_author_ids = []
        for item in self.author_list_widget.selectedItems():
            selected_author_ids.append(item.data(Qt.UserRole))

        if not title:
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return

        if self.book_data:
            # EDIT MODE
            book_id = self.book_data[0]
            success, msg = self.db.update_book(book_id, title, genre, year, selected_author_ids)
        else:
            # ADD MODE
            success, msg = self.db.add_book(title, genre, year, selected_author_ids)

        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)


class CreateClubDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Book Club")
        self.layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()

        form = QFormLayout()
        form.addRow("Club Name:", self.name_input)
        form.addRow("Description:", self.desc_input)
        self.layout.addLayout(form)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return self.name_input.text(), self.desc_input.toPlainText()


# --- LOGIN WINDOW ---
class LoginWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SmartLibrary - Login')
        self.setGeometry(300, 300, 350, 200)

        layout = QVBoxLayout()

        lbl_welcome = QLabel("<h3 style='color: #778da9;'>SmartLibrary System Login</h3>")
        lbl_welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_welcome)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_input)

        btn_login = QPushButton('Login')
        btn_login.clicked.connect(self.handle_login)
        layout.addWidget(btn_login)

        self.setLayout(layout)

    def handle_login(self):
        username = self.user_input.text()
        password = self.pass_input.text()

        user_data = self.db.authenticate_user(username, password)

        if user_data:
            self.main_window = MainWindow(user_data, self.db)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, 'Error', 'Invalid credentials')


# --- MAIN DASHBOARD ---
class MainWindow(QMainWindow):
    def __init__(self, user_data, db_manager):
        super().__init__()
        self.db = db_manager

        if user_data['role_id'] == 1:
            self.user = Librarian(user_data['id'], user_data['username'], user_data['full_name'], user_data['email'])
        else:
            self.user = Member(user_data['id'], user_data['username'], user_data['full_name'], user_data['email'])

        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"SmartLibrary - {self.user.full_name} ({self.user.__class__.__name__})")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tab_dashboard = QWidget()
        self.tab_catalog = QWidget()
        self.tab_clubs = QWidget()

        self.tabs.addTab(self.tab_dashboard, "Dashboard")
        self.tabs.addTab(self.tab_catalog, "Book Catalog")
        self.tabs.addTab(self.tab_clubs, "Book Clubs")

        if isinstance(self.user, Member):
            self.tab_loans = QWidget()
            self.tabs.addTab(self.tab_loans, "My Loans")

        layout.addWidget(self.tabs)

        self.setup_dashboard_tab()
        self.setup_catalog_tab()
        self.setup_clubs_tab()
        if isinstance(self.user, Member):
            self.setup_loans_tab()

    # ---------------- TAB 1: DASHBOARD (Styled) ----------------
    def setup_dashboard_tab(self):
        layout = QVBoxLayout()

        # 1. Top Stats Cards
        stats_layout = QHBoxLayout()

        # Use placeholders for QLabel references
        self.lbl_total_books = QLabel("...")
        self.lbl_active_members = QLabel("...")
        self.lbl_active_loans = QLabel("...")

        def create_stat_card(title, label):
            card = QGroupBox(title)
            card_layout = QVBoxLayout()
            label.setFont(QFont("Arial", 28, QFont.Bold))
            label.setStyleSheet("color: #e0e1dd;")
            label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(label)
            card.setLayout(card_layout)
            return card

        stats_layout.addWidget(create_stat_card("Total Books", self.lbl_total_books))
        stats_layout.addWidget(create_stat_card("Active Members", self.lbl_active_members))
        stats_layout.addWidget(create_stat_card("Active Loans", self.lbl_active_loans))

        layout.addLayout(stats_layout)

        # 2. Charts / Reports Section (Using two columns for popular books and clubs)
        charts_layout = QHBoxLayout()

        # Popular Books (Replaces Top Book Chart)
        popular_books_group = QGroupBox("Popular Books Report")
        self.lbl_popular_books = QLabel("Loading...")
        self.lbl_popular_books.setAlignment(Qt.AlignTop)
        self.lbl_popular_books.setWordWrap(True)
        pb_layout = QVBoxLayout(popular_books_group)
        pb_layout.addWidget(self.lbl_popular_books)
        charts_layout.addWidget(popular_books_group)

        # Book Clubs (Replaces Top Club Chart)
        club_stats_group = QGroupBox("Top Book Clubs")
        self.lbl_top_clubs = QLabel("Loading...")
        self.lbl_top_clubs.setAlignment(Qt.AlignTop)
        self.lbl_top_clubs.setWordWrap(True)
        cs_layout = QVBoxLayout(club_stats_group)
        cs_layout.addWidget(self.lbl_top_clubs)
        charts_layout.addWidget(club_stats_group)

        layout.addLayout(charts_layout)

        # 3. Librarian Report (Overdue/Members: Only shown if Librarian)
        layout.addWidget(QLabel("<h3 style='color: #e0e1dd; margin-top: 10px;'>Detailed Reports</h3>"))
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.report_table)

        btn_refresh = QPushButton("Refresh Dashboard Data")
        btn_refresh.clicked.connect(self.load_dashboard_data)
        layout.addWidget(btn_refresh)

        self.tab_dashboard.setLayout(layout)
        self.load_dashboard_data()

    def load_dashboard_data(self):
        # Update Stats Cards
        stats = self.db.get_dashboard_stats()
        self.lbl_total_books.setText(str(stats['books']))
        self.lbl_active_members.setText(str(stats['members']))
        self.lbl_active_loans.setText(str(stats['active_loans']))

        # Update Popular Books List
        popular_books = self.db.get_popular_books()
        if popular_books:
            pb_text = "<br>".join([f"• {b[0]} ({b[2]} loans)" for b in popular_books])
        else:
            pb_text = "<i>No loan data available.</i>"
        self.lbl_popular_books.setText(pb_text)

        # Update Top Clubs List (Simple member count by name)
        clubs = self.db.get_all_clubs()  # Need a method to get club members count, adapting for now
        if clubs:
            # Note: DatabaseManager.get_all_clubs doesn't return member count,
            # so we just list them for now to maintain the look.
            club_text = "<br>".join([f"• {c[1]} (Created by {c[3]})" for c in clubs[:5]])
        else:
            club_text = "<i>No clubs created yet.</i>"
        self.lbl_top_clubs.setText(club_text)

        # Load Table Data (Overdue/Popular Books)
        self.report_table.setRowCount(0)

        if isinstance(self.user, Librarian):
            self.report_table.setColumnCount(4)
            self.report_table.setHorizontalHeaderLabels(["Book", "Borrower", "Due Date", "Days Overdue"])
            data = self.db.get_overdue_books()
            cols = 4
        else:
            # Members see the Popular Books List in the table report as well
            self.report_table.setColumnCount(3)
            self.report_table.setHorizontalHeaderLabels(["Title", "Genre", "Times Borrowed"])
            data = self.db.get_popular_books()
            cols = 3

        for row_idx, row_data in enumerate(data):
            self.report_table.insertRow(row_idx)
            for col_idx in range(cols):
                self.report_table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data[col_idx])))

    # ---------------- TAB 2: CATALOG (Search & CRUD) ----------------
    def setup_catalog_tab(self):
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Title, Genre, or Author...")
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.load_books)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(btn_search)

        if isinstance(self.user, Librarian):
            btn_manage_authors = QPushButton("Manage Authors")
            btn_manage_authors.clicked.connect(self.manage_authors)
            btn_add_book = QPushButton("Add New Book")
            btn_add_book.clicked.connect(lambda: self.manage_book())
            top_layout.addWidget(btn_manage_authors)
            top_layout.addWidget(btn_add_book)

        layout.addLayout(top_layout)

        # Table
        self.book_table = QTableWidget()

        if isinstance(self.user, Librarian):
            self.book_table.setColumnCount(8)
            self.book_table.setHorizontalHeaderLabels(
                ['ID', 'Title', 'Genre', 'Year', 'Available', 'Authors', 'Edit', 'Delete'])
        else:
            self.book_table.setColumnCount(7)
            self.book_table.setHorizontalHeaderLabels(
                ['ID', 'Title', 'Genre', 'Year', 'Available', 'Authors', 'Action'])

        self.book_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.book_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.book_table.setMinimumHeight(400)
        layout.addWidget(self.book_table)

        btn_refresh_catalog = QPushButton("Refresh Catalog")
        btn_refresh_catalog.clicked.connect(self.load_books)
        layout.addWidget(btn_refresh_catalog)

        self.tab_catalog.setLayout(layout)
        self.load_books()

    def load_books(self):
        search_term = self.search_input.text()
        books = self.db.get_all_books(search_term)
        self.book_table.setRowCount(0)

        is_librarian = isinstance(self.user, Librarian)

        for row_idx, book_data in enumerate(books):
            self.book_table.insertRow(row_idx)

            # Insert Data (ID, Title, Genre, Year, Available, Authors)
            for col_idx, data in enumerate(book_data):
                self.book_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

            b_id = book_data[0]
            is_avail = book_data[4]

            if is_librarian:
                btn_edit = QPushButton("Edit")
                btn_edit.clicked.connect(lambda _, data=book_data: self.manage_book(data))
                self.book_table.setCellWidget(row_idx, 6, btn_edit)

                btn_delete = QPushButton("Delete")
                btn_delete.clicked.connect(lambda _, bid=b_id: self.delete_book(bid))
                self.book_table.setCellWidget(row_idx, 7, btn_delete)
            else:
                if is_avail:
                    btn_borrow = QPushButton("Borrow")
                    btn_borrow.clicked.connect(lambda _, bid=b_id: self.borrow_book(bid))
                    self.book_table.setCellWidget(row_idx, 6, btn_borrow)
                else:
                    lbl = QLabel("Unavailable")
                    lbl.setAlignment(Qt.AlignCenter)
                    self.book_table.setCellWidget(row_idx, 6, lbl)

    def manage_authors(self):
        dlg = AuthorManagementDialog(self.db, self)
        dlg.exec_()
        self.load_books()

    def manage_book(self, book_data=None):
        dlg = BookManagementDialog(self.db, book_data, self)
        if dlg.exec_():
            self.load_books()
            self.load_dashboard_data()

    def delete_book(self, book_id):
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     "Are you sure you want to delete this book? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success, message = self.db.delete_book(book_id)
            if success:
                QMessageBox.information(self, "Success", message)
                self.load_books()
                self.load_dashboard_data()
            else:
                QMessageBox.warning(self, "Error", message)

    # ---------------- TAB 3: BOOK CLUBS ----------------
    def setup_clubs_tab(self):
        layout = QVBoxLayout()

        controls = QHBoxLayout()
        btn_create = QPushButton("Create New Club")
        btn_create.clicked.connect(self.create_club)
        btn_members = QPushButton("View Members of Selected Club")
        btn_members.clicked.connect(self.view_club_members)
        controls.addWidget(btn_create)
        controls.addWidget(btn_members)
        layout.addLayout(controls)

        self.club_table = QTableWidget()
        self.club_table.setColumnCount(5)
        self.club_table.setHorizontalHeaderLabels(['ID', 'Club Name', 'Description', 'Creator', 'Action'])
        self.club_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.club_table.setMinimumHeight(400)
        layout.addWidget(self.club_table)

        btn_refresh = QPushButton("Refresh Clubs")
        btn_refresh.clicked.connect(self.load_clubs)
        layout.addWidget(btn_refresh)

        self.tab_clubs.setLayout(layout)
        self.load_clubs()

    def load_clubs(self):
        clubs = self.db.get_all_clubs()
        self.club_table.setRowCount(0)

        for row_idx, club in enumerate(clubs):
            self.club_table.insertRow(row_idx)
            for col_idx, data in enumerate(club):
                self.club_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

            c_id = club[0]
            btn_join = QPushButton("Join")
            btn_join.clicked.connect(lambda _, cid=c_id: self.join_club(cid))
            self.club_table.setCellWidget(row_idx, 4, btn_join)

    def create_club(self):
        dlg = CreateClubDialog(self)
        if dlg.exec_():
            name, desc = dlg.get_data()
            if name:
                success, msg = self.db.create_club(name, desc, self.user.id)
                if success:
                    QMessageBox.information(self, "Success", msg)
                    self.load_clubs()
                    self.load_dashboard_data()
                else:
                    QMessageBox.warning(self, "Error", msg)

    def join_club(self, club_id):
        success, msg = self.db.join_club(self.user.id, club_id)
        QMessageBox.information(self, "Club Membership", msg)

    def view_club_members(self):
        row = self.club_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Club", "Please select a club row first.")
            return

        club_id = self.club_table.item(row, 0).text()
        club_name = self.club_table.item(row, 1).text()
        members = self.db.get_club_members(club_id)

        msg_text = f"--- Members of {club_name} ---\n\n" + "\n".join(
            [f"• {m[0]} ({m[1]}) joined on {m[2]}" for m in members])
        if len(members) == 0: msg_text = f"--- Members of {club_name} ---\n\nNo members yet."
        QMessageBox.information(self, "Club Members", msg_text)

    # ---------------- TAB 4: MY LOANS (Members Only) ----------------
    def setup_loans_tab(self):
        layout = QVBoxLayout()

        btn_refresh = QPushButton("Refresh My Loans")
        btn_refresh.clicked.connect(self.load_loans)
        layout.addWidget(btn_refresh)

        self.loan_table = QTableWidget()
        self.loan_table.setColumnCount(5)
        self.loan_table.setHorizontalHeaderLabels(['Loan ID', 'Book', 'Borrow Date', 'Due Date', 'Action'])
        self.loan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.loan_table.setMinimumHeight(400)
        layout.addWidget(self.loan_table)

        self.tab_loans.setLayout(layout)
        self.load_loans()

    def load_loans(self):
        loans = self.db.get_user_loans(self.user.id)
        self.loan_table.setRowCount(0)
        for row_idx, loan in enumerate(loans):
            self.loan_table.insertRow(row_idx)
            for col_idx in range(4):
                self.loan_table.setItem(row_idx, col_idx, QTableWidgetItem(str(loan[col_idx])))
            l_id = loan[0]
            btn_return = QPushButton("Return")
            btn_return.clicked.connect(lambda _, lid=l_id: self.return_book(lid))
            self.loan_table.setCellWidget(row_idx, 4, btn_return)

    # --- SHARED ACTIONS ---
    def borrow_book(self, book_id):
        success, message = self.db.borrow_book(self.user.id, book_id)
        if success:
            QMessageBox.information(self, "Success", message)
            self.load_books()
            self.load_dashboard_data()
            if isinstance(self.user, Member): self.load_loans()
        else:
            QMessageBox.warning(self, "Error", message)

    def return_book(self, loan_id):
        success, message = self.db.return_book(loan_id)
        if success:
            QMessageBox.information(self, "Success", message)
            if isinstance(self.user, Member): self.load_loans()
            self.load_books()
            self.load_dashboard_data()
        else:
            QMessageBox.warning(self, "Error", message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)  # Apply the custom style globally

    db = DatabaseManager()
    if db.conn:
        login = LoginWindow(db)
        login.show()
        sys.exit(app.exec_())
    else:
        QMessageBox.critical(None, "Database Error",
                             "Failed to connect to the SmartLibrary Database. Please check 'databasemanager.py' credentials and ensure PostgreSQL is running.")
        sys.exit(1)