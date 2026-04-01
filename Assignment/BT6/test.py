"""
Test script for Student Management System
Tests B-Tree indexing and database operations
"""

from database import StudentDatabase, Student
import os


TEST_DB_FILE = "students_test.db"

def test_database():
    """Test database operations"""
    # Remove old database files
    for f in [TEST_DB_FILE]:
        if os.path.exists(f):
            os.remove(f)
    
    # Create new database
    db = StudentDatabase(db_file=TEST_DB_FILE, auto_seed=False)
    print("[OK] Database created successfully\n")
    
    # Test 1: Add students
    print("=" * 60)
    print("TEST 1: Adding Students")
    print("=" * 60)
    
    students_data = [
        (1001, "Nguyễn Văn A", "M", "2003-05-15", 3.8, "0912345678"),
        (1002, "Trần Thị B", "F", "2003-08-22", 3.6, "0987654321"),
        (1003, "Lê Văn C", "M", "2002-12-10", 3.9, "0901234567"),
        (1004, "Phạm Thị D", "F", "2003-03-18", 3.5, "0923456789"),
        (1005, "Hoàng Văn E", "M", "2003-07-25", 3.7, "0934567890"),
    ]
    
    for sid, name, gender, dob, gpa, phone in students_data:
        student = Student(sid, name, gender, dob, gpa, phone)
        success, msg = db.add_student(student)
        print(f"Added: {name:20} (ID: {sid}) - {msg}")
        status = db.validate_indexes()
        if not (status["id"]["ok"] and status["name"]["ok"]):
            raise RuntimeError(f"Index validation failed after insert {sid}: {status}")
    
    print("\n" + "=" * 60)
    print("TEST 2: View All Students")
    print("=" * 60)
    all_students = db.get_all_students()
    for i, student in enumerate(all_students, 1):
        print(f"{i}. {student.name:20} ID:{student.student_id} GPA:{student.gpa:.1f}")
    
    print("\n" + "=" * 60)
    print("TEST 3: Search by Student ID")
    print("=" * 60)
    search_ids = [1003, 1005, 9999]
    for sid in search_ids:
        student = db.search_by_id(sid)
        if student:
            print(f"[OK] Found ID {sid}: {student.name} - GPA: {student.gpa:.1f}")
        else:
            print(f"[NO] ID {sid}: Not found")
    
    print("\n" + "=" * 60)
    print("TEST 4: Search by Name (Partial Match)")
    print("=" * 60)
    search_names = ["Trần", "Văn", "Đỗ"]
    for name in search_names:
        students = db.search_by_name(name)
        if students:
            print(f"[OK] Found '{name}': {len(students)} student(s)")
            for s in students:
                print(f"  - {s.name} (ID: {s.student_id})")
        else:
            print(f"[NO] Found '{name}': No students")
    
    print("\n" + "=" * 60)
    print("TEST 5: B-Tree Index Information")
    print("=" * 60)
    print("\nID Index entries:")
    id_entries = db.get_id_index_info()
    for i, (key, sid) in enumerate(id_entries, 1):
        print(f"  {i}. Key: {key}, Student ID: {sid}")
    
    print("\nName Index entries:")
    name_entries = db.get_name_index_info()
    for i, (key, sid) in enumerate(name_entries, 1):
        display_key = key[0] if isinstance(key, tuple) else key
        print(f"  {i}. Key: '{display_key}', Student ID: {sid}")

    print("\n" + "=" * 60)
    print("TEST 5.1: Duplicate Name Should Not Overwrite Index")
    print("=" * 60)
    dup_a = Student(1101, "Nguyễn Văn A", "M", "2003-01-01", 3.2, "0900000001")
    dup_b = Student(1102, "Nguyễn Văn A", "F", "2003-01-02", 3.3, "0900000002")
    _, msg_a = db.add_student(dup_a)
    _, msg_b = db.add_student(dup_b)
    print(f"Add ID 1101: {msg_a}")
    print(f"Add ID 1102: {msg_b}")

    name_entries = db.get_name_index_info()
    a_keys = [sid for key, sid in name_entries if isinstance(key, tuple) and key[0] == "nguyễn văn a"]
    print(f"Name-index entries for 'nguyễn văn a': {a_keys}")
    if 1101 not in a_keys or 1102 not in a_keys:
        raise RuntimeError("Name index overwritten duplicate-name entry unexpectedly")

    status = db.validate_indexes()
    if not (status["id"]["ok"] and status["name"]["ok"]):
        raise RuntimeError(f"Index validation failed on duplicate-name check: {status}")
    
    print("\n" + "=" * 60)
    print("TEST 6: Delete Student")
    print("=" * 60)
    delete_id = 1002
    student_to_delete = db.search_by_id(delete_id)
    if student_to_delete:
        print(f"Deleting: {student_to_delete.name} (ID: {delete_id})")
        success, msg = db.delete_student(delete_id)
        print(f"Result: {msg}")
        status = db.validate_indexes()
        if not (status["id"]["ok"] and status["name"]["ok"]):
            raise RuntimeError(f"Index validation failed after delete {delete_id}: {status}")
    
    print("\nRemaining students:")
    all_students = db.get_all_students()
    for i, student in enumerate(all_students, 1):
        print(f"{i}. {student.name:20} ID:{student.student_id}")
    
    print("\n" + "=" * 60)
    print("TEST 7: Add Another Student (After Delete)")
    print("=" * 60)
    new_student = Student(1006, "Vũ Văn F", "M", "2003-11-30", 3.4, "0945678901")
    success, msg = db.add_student(new_student)
    print(f"Added: Vũ Văn F (ID: 1006) - {msg}")
    
    print("\nFinal ID Index:")
    id_entries = db.get_id_index_info()
    for i, (key, sid) in enumerate(id_entries, 1):
        student = db.students.get(sid)
        print(f"  {i}. ID: {key} -> {student.name}")
    
    print("\n" + "=" * 60)
    print("TEST 8: Data Persistence")
    print("=" * 60)
    print("Creating new database instance from saved files...")
    db2 = StudentDatabase(db_file=TEST_DB_FILE, auto_seed=False)
    students_from_disk = db2.get_all_students()
    print(f"[OK] Loaded {len(students_from_disk)} students from disk")
    for student in students_from_disk:
        print(f"  - {student.name} (ID: {student.student_id})")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    # Clean up isolated test database to avoid affecting app runs.
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


if __name__ == "__main__":
    test_database()
