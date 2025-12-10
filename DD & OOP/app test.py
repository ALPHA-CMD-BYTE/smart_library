from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFormLayout, QGroupBox, QInputDialog, QSpacerItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from databasemanager import databasemanager
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet
from PyQt5.QtGui import QPainter

# Beautiful Blue-White-Black Theme
STYLE = """
    QMainWindow {
        background-color: #0d1b2a;
    }
    QLabel {
        color: #e0e1dd;
        font-size: 14px;
    }
    QLineEdit, QComboBox {
        background-color: #1b263b;
        color: #e0e1dd;
        border: 2px solid #415a77;
        border-radius: 10px;
        padding: 10px;
        font-size: 14px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #778da9;
    }
    QPushButton {
        background-color: #415a77;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #778da9;
    }
    QPushButton:pressed {
        background-color: #33415c;
    }
    QTabWidget::pane {
        border: 1px solid #415a77;
        background-color: #1b263b;
        border-radius: 12px;
    }
    QTabBar::tab {
        background: #1b263b;
        color: #e0e1dd;
        padding: 14px 24px;
        margin: 2px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
    QTabBar::tab:selected {
        background: #415a77;
        color: white;
        font-weight: bold;
    }
    QTableWidget {
        background-color: #1b263b;
        gridline-color: #33415c;
        color: #e0e1dd;
        font-size: 13px;
    }
    QHeaderView::section {
        background-color: #415a77;
        color: white;
        padding: 12px;
        font-weight: bold;
    }
    QGroupBox {
        font-weight: bold;
        color: #778da9;
        border: 2px solid #415a77;
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 10px;
    }
"""


class SmartLibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dao = SmartLibManagerDAO()
        self.current_user = None
        self.current_role = None

        self.setWindowTitle("SmartLibrary – Limkokwing University Sierra Leone")
        self.setGeometry(100, 100, 1200, 750)
        self.setStyleSheet(STYLE)

        # Set Fusion style for better dark theme support
        app.setStyle('Fusion')

        self.init_login()

    def init_login(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(350, 120, 350, 120)
        layout.setSpacing(20)

        # Title
        title = QLabel("SMARTLIBRARY")
        title.setFont(QFont("Segoe UI", 36, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #778da9; letter-spacing: 3px;")

        subtitle = QLabel("Limkokwing University Sierra Leone")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #415a77; font-size: 16px; margin-bottom: 30px;")

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(20)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Librarian", "Member"])
        self.role_combo.setCurrentText("Member")

        form.addRow("Username:", self.username_edit)
        form.addRow("Password:", self.password_edit)
        form.addRow("Login as:", self.role_combo)

        login_btn = QPushButton("LOGIN TO SYSTEM")
        login_btn.setFixedHeight(55)
        login_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        login_btn.clicked.connect(self.authenticate)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(login_btn)
        layout.addStretch()

        widget.setLayout(layout)

    def authenticate(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        role = 1 if self.role_combo.currentText() == "Librarian" else 2

        self.dao.cursor.execute(
            "SELECT id, full_name, role_id FROM Users WHERE username = %s AND password_hash = %s AND role_id = %s",
            (username, password, role)
        )
        user = self.dao.cursor.fetchone()

        if user:
            self.current_user = user
            self.current_role = "Librarian" if user['role_id'] == 1 else "Member"
            QMessageBox.information(self, "Welcome!",
                                    f"Login Successful!\nWelcome back, {user['full_name']}!")
            self.show_main_interface()
        else:
            QMessageBox.critical(self, "Access Denied", "Invalid username or password!")

    def show_main_interface(self):
        self.setCentralWidget(QWidget())
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel(f"SmartLibrary Dashboard — {self.current_user['full_name']} ({self.current_role})")
        header.setStyleSheet(
            "font-size: 20px; color: #778da9; padding: 15px; background: #1b263b; border-radius: 12px;")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setFont(QFont("Segoe UI", 11))

        tabs.addTab(self.catalog_tab(), "  Book Catalog  ")
        tabs.addTab(self.loan_tab(), "  Borrow & Return  ")
        if self.current_role == "Librarian":
            tabs.addTab(self.add_book_tab(), "  Add New Book  ")
        tabs.addTab(self.club_tab(), "  Book Clubs  ")
        tabs.addTab(self.dashboard_tab(), "  Dashboard  ")

        main_layout.addWidget(tabs)
        self.centralWidget().setLayout(main_layout)

    # — All your previous methods (catalog_tab, load_catalog, borrow_book, etc.) stay EXACTLY the same —
    # Only visual changes above. Copy them from the previous version.

    def catalog_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        search_bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search books by title...")
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.load_catalog)
        search_bar.addWidget(self.search_edit)
        search_bar.addWidget(search_btn)

        self.catalog_table = QTableWidget(0, 5)
        self.catalog_table.setHorizontalHeaderLabels(["ID", "Title", "Genre", "Year", "Status"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(search_bar)
        layout.addWidget(self.catalog_table)
        widget.setLayout(layout)
        self.load_catalog()
        return widget

    def load_catalog(self):
        keyword = self.search_edit.text().strip()
        query = "SELECT id, title, genre, publication_year, available FROM Books WHERE title ILIKE %s ORDER BY title"
        self.dao.cursor.execute(query, (f"%{keyword}%",))
        books = self.dao.cursor.fetchall()

        self.catalog_table.setRowCount(len(books))
        for i, b in enumerate(books):
            status = "Available" if b['available'] else "Borrowed"
            color = "#4CAF50" if b['available'] else "#f44336"
            self.catalog_table.setItem(i, 0, QTableWidgetItem(str(b['id'])))
            self.catalog_table.setItem(i, 1, QTableWidgetItem(b['title']))
            self.catalog_table.setItem(i, 2, QTableWidgetItem(b['genre'] or "—"))
            self.catalog_table.setItem(i, 3, QTableWidgetItem(str(b['publication_year'] or "—")))
            item = QTableWidgetItem(status)
            item.setBackground(QColor(color))
            item.setForeground(QColor("white"))
            item.setTextAlignment(Qt.AlignCenter)
            self.catalog_table.setItem(i, 4, item)

    def loan_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        box = QGroupBox("Borrow or Return a Book")
        form = QFormLayout()

        self.member_id_edit = QLineEdit()
        self.book_id_edit = QLineEdit()

        borrow_btn = QPushButton("Borrow Book")
        return_btn = QPushButton("Return Book")
        borrow_btn.clicked.connect(self.borrow_book)
        return_btn.clicked.connect(self.return_book)

        hbox = QHBoxLayout()
        hbox.addWidget(borrow_btn)
        hbox.addWidget(return_btn)

        form.addRow("Member ID:", self.member_id_edit)
        form.addRow("Book ID:", self.book_id_edit)
        form.addRow(hbox)

        box.setLayout(form)
        layout.addWidget(box)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def add_book_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        box = QGroupBox("Add New Book to Library")
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.genre_edit = QLineEdit()
        self.year_edit = QLineEdit()

        add_btn = QPushButton("Add Book")
        add_btn.setFixedHeight(50)
        add_btn.clicked.connect(self.add_book)

        form.addRow("Title:", self.title_edit)
        form.addRow("Genre:", self.genre_edit)
        form.addRow("Year:", self.year_edit)
        form.addRow(add_btn)

        box.setLayout(form)
        layout.addWidget(box)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def add_book(self):
        title = self.title_edit.text().strip()
        genre = self.genre_edit.text().strip()
        year = self.year_edit.text().strip()

        if not title or not year.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Title and year are required!")
            return

        try:
            self.dao.create_book(title, genre or None, int(year))
            QMessageBox.information(self, "Success", f"Book '{title}' added successfully!")
            self.title_edit.clear()
            self.genre_edit.clear()
            self.year_edit.clear()
            self.load_catalog()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    # borrow_book, return_book, club_tab, dashboard_tab → same as before

    def borrow_book(self):
        try:
            member_id = int(self.member_id_edit.text())
            book_id = int(self.book_id_edit.text())
            self.dao.create_loan(book_id, member_id)
            QMessageBox.information(self, "Success", "Book borrowed!")
            self.load_catalog()
        except ValueError as e:
            QMessageBox.warning(self, "Failed", str(e))

    def return_book(self):
        loan_id, ok = QInputDialog.getText(self, "Return Book", "Enter Loan ID to return:")
        if ok and loan_id.strip():
            try:
                self.dao.update_loan_return(int(loan_id))
                QMessageBox.information(self, "Returned", "Book returned successfully!")
                self.load_catalog()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ==================== BOOK CLUB FULL FEATURES ====================
    def club_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # --- Create Club Section (Librarian + Member) ---
        create_box = QGroupBox("Create New Book Club")
        create_form = QFormLayout()
        self.club_name_edit = QLineEdit()
        self.club_desc_edit = QLineEdit()
        create_btn = QPushButton("Create Club")
        create_btn.clicked.connect(self.create_club)
        create_form.addRow("Club Name:", self.club_name_edit)
        create_form.addRow("Description:", self.club_desc_edit)
        create_form.addRow(create_btn)
        create_box.setLayout(create_form)

        # --- Join Club Section ---
        join_box = QGroupBox("Join Existing Club")
        join_layout = QHBoxLayout()
        self.join_club_id = QLineEdit()
        self.join_club_id.setPlaceholderText("Enter Club ID")
        join_btn = QPushButton("Join Club")
        join_btn.clicked.connect(self.join_club)
        join_layout.addWidget(QLabel("Club ID:"))
        join_layout.addWidget(self.join_club_id)
        join_layout.addWidget(join_btn)
        join_box.setLayout(join_layout)

        # --- List All Clubs ---
        self.clubs_table = QTableWidget(0, 4)
        self.clubs_table.setHorizontalHeaderLabels(["Club ID", "Name", "Description", "Members"])
        self.clubs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        refresh_btn = QPushButton("Refresh Club List")
        refresh_btn.clicked.connect(self.load_clubs)

        layout.addWidget(create_box)
        layout.addWidget(join_box)
        layout.addWidget(refresh_btn)
        layout.addWidget(self.clubs_table)
        layout.addStretch()
        widget.setLayout(layout)

        self.load_clubs()  # Load clubs on tab open
        return widget

    def create_club(self):
        name = self.club_name_edit.text().strip()
        desc = self.club_desc_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Club name is required!")
            return
        try:
            club_id = self.dao.create_book_club(name, desc, self.current_user['id'])
            QMessageBox.information(self, "Success", f"Club '{name}' created with ID: {club_id}")
            self.club_name_edit.clear()
            self.club_desc_edit.clear()
            self.load_clubs()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def join_club(self):
        club_id_text = self.join_club_id.text().strip()
        if not club_id_text.isdigit():
            QMessageBox.warning(self, "Error", "Valid Club ID required!")
            return
        try:
            self.dao.create_club_membership(int(club_id_text), self.current_user['id'])
            QMessageBox.information(self, "Success", "You have joined the club!")
            self.join_club_id.clear()
            self.load_clubs()
        except Exception as e:
            QMessageBox.critical(self, "Failed", str(e))

    def load_clubs(self):
        query = """
            SELECT bc.id, bc.name, bc.description, COUNT(cm.user_id) as members
            FROM BookClubs bc
            LEFT JOIN ClubMemberships cm ON bc.id = cm.club_id
            GROUP BY bc.id, bc.name, bc.description
            ORDER BY bc.id
        """
        self.dao.cursor.execute(query)
        clubs = self.dao.cursor.fetchall()

        self.clubs_table.setRowCount(len(clubs))
        for i, club in enumerate(clubs):
            self.clubs_table.setItem(i, 0, QTableWidgetItem(str(club['id'])))
            self.clubs_table.setItem(i, 1, QTableWidgetItem(club['name']))
            self.clubs_table.setItem(i, 2, QTableWidgetItem(club['description'] or "No description"))
            self.clubs_table.setItem(i, 3, QTableWidgetItem(str(club['members'])))
    def dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        title = QLabel("LIBRARY DASHBOARD")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #778da9;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # === Stats Cards (Safe & Beautiful) ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(25)

        total_books = self.get_count("SELECT COUNT(*) FROM Books")
        available_books = self.get_count("SELECT COUNT(*) FROM Books WHERE available = TRUE")
        borrowed_books = total_books - available_books
        total_members = self.get_count("SELECT COUNT(*) FROM Users WHERE role_id = 2")
        total_clubs = self.get_count("SELECT COUNT(*) FROM BookClubs")
        overdue = self.get_count("SELECT COUNT(*) FROM Loans WHERE return_date IS NULL AND due_date < CURRENT_DATE")

        cards = [
            ("Total Books", total_books, "#415a77"),
            ("Available", available_books, "#4CAF50"),
            ("Borrowed", borrowed_books, "#FF5722"),
            ("Members", total_members, "#2196F3"),
            ("Clubs", total_clubs, "#9C27B0"),
            ("Overdue", overdue, "#F44336"),
        ]

        for label, value, color in cards:
            card = QLabel(f"{label}\n{value}")
            card.setStyleSheet(f"""
                background: {color}; color: white; font-size: 20px; font-weight: bold;
                border-radius: 15px; padding: 25px; text-align: center;
            """)
            card.setAlignment(Qt.AlignCenter)
            card.setFixedHeight(130)
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # === Simple Text Summary (No Charts = No Crash!) ===
        summary_box = QGroupBox("Library Summary")
        summary_layout = QVBoxLayout()

        top_books = self.get_top_books()
        top_clubs = self.get_top_clubs()

        summary_text = f"""
        <h3>Most Popular Books</h3>
        {top_books}
        <br>
        <h3>Most Active Clubs</h3>
        {top_clubs}
        <br>
        <p style='color:#778da9;'><i>SmartLibrary System • Limkokwing University Sierra Leone</i></p>
        """.strip()

        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-size: 15px; color: #e0e1dd;")
        summary_label.setOpenExternalLinks(False)
        summary_layout.addWidget(summary_label)
        summary_box.setLayout(summary_layout)
        layout.addWidget(summary_box)

        widget.setLayout(layout)
        return widget

    def get_count(self, query):
        try:
            self.dao.cursor.execute(query)
            result = self.dao.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

    def get_top_books(self):
        try:
            self.dao.cursor.execute("""
                SELECT b.title, COUNT(l.id) as count
                FROM Books b LEFT JOIN Loans l ON b.id = l.book_id
                GROUP BY b.id, b.title
                ORDER BY count DESC LIMIT 5
            """)
            rows = self.dao.cursor.fetchall()
            if not rows:
                return "<i>No loans recorded yet</i>"
            return "<br>".join([f"• {r['title']} — {r['count']} loans" for r in rows])
        except:
            return "<i>Unable to load book stats</i>"

    def get_top_clubs(self):
        try:
            self.dao.cursor.execute("""
                SELECT bc.name, COUNT(cm.user_id) as members
                FROM BookClubs bc LEFT JOIN ClubMemberships cm ON bc.id = cm.club_id
                GROUP BY bc.id, bc.name
                ORDER BY members DESC LIMIT 5
            """)
            rows = self.dao.cursor.fetchall()
            if not rows:
                return "<i>No clubs created yet</i>"
            return "<br>".join([f"• {r['name']} — {r['members']} members" for r in rows])
        except:
            return "<i>Unable to load club stats</i>"
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SmartLibraryApp()
    window.show()
    sys.exit(app.exec_())