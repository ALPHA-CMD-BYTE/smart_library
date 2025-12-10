Create the database smart_library;


SET search_path to smart_library, public;

-- Roles (Authentication/User Roles) [cite: 35]
CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Users (Combines Members & Authentication) [cite: 32, 35]
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, 
    role_id INT NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES Roles(id) ON DELETE RESTRICT
);

-- Authors [cite: 31]
CREATE TABLE Authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    bio TEXT
);

-- Books [cite: 30]
CREATE TABLE Books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    genre VARCHAR(50),
    publication_year INT,
    available BOOLEAN DEFAULT TRUE NOT NULL 
);

-- BookAuthors (Many-to-Many Relationship) [cite: 48]
CREATE TABLE BookAuthors (
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES Books(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES Authors(id) ON DELETE CASCADE
);

-- Loans [cite: 34]
CREATE TABLE Loans (
    id SERIAL PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    borrow_date DATE DEFAULT CURRENT_DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE, -- NULL means the book is currently borrowed (active loan)
    CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES Books(id) ON DELETE RESTRICT,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT,
    CONSTRAINT check_due CHECK (due_date = borrow_date + INTERVAL '7 days') -- [cite: 147]
);

-- BookClubs [cite: 33]
CREATE TABLE BookClubs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_by INT NOT NULL,
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE RESTRICT
);

-- ClubMemberships
CREATE TABLE ClubMemberships (
    id SERIAL PRIMARY KEY,
    club_id INT NOT NULL,
    user_id INT NOT NULL,
    join_date DATE DEFAULT CURRENT_DATE,
    UNIQUE (club_id, user_id),
    FOREIGN KEY (club_id) REFERENCES BookClubs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- 3. TRIGGERS AND FUNCTIONS (Advanced SQL) 

-- Function: Automatically update book availability to FALSE when borrowed
CREATE OR REPLACE FUNCTION update_book_on_borrow()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Books SET available = FALSE WHERE id = NEW.book_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Automatically update book availability to TRUE when returned
CREATE OR REPLACE FUNCTION update_book_on_return()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.return_date IS NOT NULL AND OLD.return_date IS NULL THEN
        UPDATE Books SET available = TRUE WHERE id = NEW.book_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Enforce Max 3 Loans Rule [cite: 146]
CREATE OR REPLACE FUNCTION prevent_excess_loans()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM Loans WHERE user_id = NEW.user_id AND return_date IS NULL) >= 3 THEN
        RAISE EXCEPTION 'Member cannot have more than 3 active loans';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply Triggers
CREATE TRIGGER tr_book_borrow AFTER INSERT ON Loans FOR EACH ROW EXECUTE FUNCTION update_book_on_borrow();
CREATE TRIGGER tr_book_return AFTER UPDATE OF return_date ON Loans FOR EACH ROW EXECUTE FUNCTION update_book_on_return();
CREATE TRIGGER enforce_loan_limit BEFORE INSERT ON Loans FOR EACH ROW EXECUTE FUNCTION prevent_excess_loans();

-- 4. DATA INSERTION

-- Insert Roles
INSERT INTO Roles (name) VALUES ('Librarian'), ('Member');

-- Insert Authors
INSERT INTO Authors (name, bio) VALUES
('Chinua Achebe', 'Nigerian novelist, known for "Things Fall Apart".'),
('Chimamanda Ngozi Adichie', 'Nigerian novelist, known for "Half of a Yellow Sun".'),
('James Clear', 'Author of "Atomic Habits".'),
('Robert Kiyosaki', 'Author of "Rich Dad Poor Dad".'),
('Yuval Noah Harari', 'Author of "Sapiens".'),
('George Orwell', 'Author of "1984".'),
('Harper Lee', 'Author of "To Kill a Mockingbird".'),
('Jane Austen', 'Author of "Pride and Prejudice".'),
('F. Scott Fitzgerald', 'Author of "The Great Gatsby".'),
('Masashi Kishimoto', 'Creator of Naruto.'),
('Eiichiro Oda', 'Creator of One Piece.');

-- Insert Users (Librarians and Members)
INSERT INTO Users (username, password_hash, full_name, email, role_id) VALUES
('benefit_jr', '5440', 'Osman Sheriff', 'osmansheriff@limkokwing.sl', 1),
('Henry_Faylo', '5437', 'Henry Bangura', 'henryb@limkokwing.sl', 1),
('benefit_jr', '1234', 'Mohamed Kamara', 'mohamed@limkokwing.sl', 2),
('Selwyn', 'sel123', 'Selwyn Sheriff', 'selwyn@gmail.com', 2),
('mohamed_koroma', 'mohamed123', 'Mohamed Koroma', 'mohamed@gmail.com', 2),
('zainab_kamara', 'zainab123', 'Zainab Kamara', 'zainab@gmail.com', 2);




-- Insert Books
INSERT INTO Books (title, genre, publication_year, available) VALUES
('Things Fall Apart', 'African Literature', 1958, TRUE),
('Half of a Yellow Sun', 'Historical Fiction', 2006, TRUE),
('Americanah', 'Contemporary Fiction', 2013, TRUE),
('Atomic Habits', 'Self-Help', 2018, TRUE),
('Rich Dad Poor Dad', 'Finance', 1997, TRUE),
('Sapiens: A Brief History of Humankind', 'Non-Fiction', 2011, TRUE),
('1984', 'Dystopian', 1949, TRUE),
('To Kill a Mockingbird', 'Classic', 1960, TRUE),
('Pride and Prejudice', 'Romance', 1813, TRUE),
('The Great Gatsby', 'Classic', 1925, TRUE),
('Naruto Vol.1', 'Manga', 1999, TRUE),
('One Piece Vol.1', 'Manga', 1997, TRUE);

-- Link Authors to Books
INSERT INTO BookAuthors (book_id, author_id) VALUES
(1, 1), (2, 2), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10), (12, 11);

-- Insert BookClubs
INSERT INTO BookClubs (name, description, created_by) VALUES
('Manga Lovers Club', 'Weekly manga discussions', 1),
('African Literature Circle', 'Reading Chinua Achebe, Adichie, etc.', 2),
('Self-Improvement Society', 'Atomic Habits, Rich Dad Poor Dad', 3);

-- Insert Club Memberships
INSERT INTO ClubMemberships (club_id, user_id) VALUES
(1, 3), (1, 4), (2, 5), (3, 6);

-- 5. VIEWS [cite: 60]

CREATE OR REPLACE VIEW OverdueBooksReport AS
SELECT b.title, u.full_name, l.due_date, (CURRENT_DATE - l.due_date) AS days_overdue
FROM Loans l
JOIN Books b ON l.book_id = b.id
JOIN Users u ON l.user_id = u.id
WHERE l.return_date IS NULL AND l.due_date < CURRENT_DATE;