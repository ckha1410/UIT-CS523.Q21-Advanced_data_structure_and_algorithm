# Student Management System with B-Tree Indexing

## Overview
This project now runs as a **web app** with a modern UI (Vue + Tailwind via CDN) and a lightweight Python API server (Flask).

Core assignment logic is unchanged:
- Custom binary database storage
- Order-3 B-Tree index by Student ID
- Order-3 B-Tree index by Student Name key `(name_lower, student_id)`
- Add / Delete / Search / Self-check operations

## Key Features

### 1. **B-Tree Implementation**
- **Order 3 B-Tree**: Each internal node can have at most 2 keys and 3 children
- Efficient search and insert operations with O(log n) complexity
- Two separate B-Tree indexes for different search criteria

### 2. **Data Management**
- **Binary File Storage**: Student data is stored in binary format (not text)
- **Record Structure**: Each student record contains:
  - Student ID (4 bytes)
  - Name (50 bytes)
  - Gender (1 byte - M/F)
  - Date of Birth (10 bytes - YYYY-MM-DD)
  - GPA (4 bytes - float)
  - Phone (15 bytes)
  - **Total: 84 bytes per record**

### 3. **Operations Supported**
- **Add Student**: Insert a new student with all details
- **Delete Student**: Remove student by ID (updates both indexes)
- **Search by ID**: Fast O(log n) search using ID index
- **Search by Name**: Partial name matching across all students

### 4. **Web Interface**
Single-page dashboard with:
1. Add student form
2. Search by ID / Name and delete by ID
3. Student table
4. ID and Name index visualization (JSON view)
5. B-Tree self-check panel

## File Structure

```
BT6/
├── btree.py          # B-Tree implementation (BTreeNode and BTree classes)
├── database.py       # Database management and binary file I/O
├── web_app.py        # Flask API server + static web host
├── web/
│   └── index.html    # Vue + Tailwind frontend (CDN, no npm build)
├── requirements.txt  # Python dependencies
├── test.py           # Regression tests
├── run.bat           # Windows launcher
├── students.db       # Binary file storing student records (auto-created)
└── README.md         # This file
```

## Running the Application

1. Make sure you have Python 3.8+ installed
2. Install dependency:

```bash
pip install -r requirements.txt
```

### On Windows:
```bash
python web_app.py
```

Then open: `http://127.0.0.1:5000`

Or double-click `run.bat`.

### On Linux/Mac:
```bash
python3 web_app.py
```

## How to Use

### Adding a Student:
1. Fill all fields in the left panel
2. Click **Add**

### Searching:
1. Search by ID (exact) or Name (partial)
2. Results appear in **Search Result**

### Deleting:
1. Enter ID in Delete field
2. Click **Delete**

### Validation:
1. Click **Run B-Tree Self-Check**
2. Inspect ID/Name index status in **Self-Check Result**

## B-Tree Characteristics

### Node Structure (Order 3)
- **Maximum keys per node**: 2
- **Maximum children per node**: 3
- **Minimum keys per node** (except root): 1
- **Minimum children per node** (except root): 2

### Operations Complexity
- **Insert**: O(log n)
- **Delete**: Direct B-Tree deletion with node rebalance (borrow/merge)
- **Search**: O(log n)

## Binary File Details

### students.db
- Stores all student records sequentially
- Each record is exactly 84 bytes
- Format: ID(4) | Name(50) | Gender(1) | DOB(10) | GPA(4) | Phone(15)

### Data Persistence
- All changes are automatically saved to binary files
- Database is automatically loaded when the application starts
- No data loss between sessions

## Example Usage Flow

1. **Start the application** → Empty database
2. **Add several students** → Records saved to students.db
3. **View Student Data tab** → All students displayed
4. **Search by ID** → Uses B-Tree index for fast lookup
5. **Search by name** → Searches through all records
6. **Delete a student** → Record removed from both table and indexes
7. **Close and reopen** → All data persists from previous session

## Technical Details

### B-Tree Index Usage
- **ID Index**: Keys are student IDs (numeric), values are student IDs
- **Name Index**: Keys are `(name_lowercase, student_id)`, values are student IDs
- Both indexes use the same B-Tree structure with order 3

### Database Class Methods
- `add_student(student)`: Add new student
- `delete_student(student_id)`: Delete by ID
- `search_by_id(student_id)`: Find student by ID
- `search_by_name(name)`: Find students by name
- `get_all_students()`: Retrieve all students
- `load_database()`: Load from binary files
- `save_database()`: Save to binary files

## Validation Rules
- **Student ID**: Must be unique and numeric
- **Name**: Cannot be empty
- **GPA**: Must be between 0 and 4.0
- **Date of Birth**: Must be in YYYY-MM-DD format
- **Phone**: Cannot be empty

## Notes
- Frontend uses CDN assets (Vue, Tailwind), so no npm install/build is required.
- B-Tree and database logic are still entirely in Python.
- Database is saved to disk after each modification.
