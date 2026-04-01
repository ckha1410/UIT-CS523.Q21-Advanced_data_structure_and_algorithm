"""
Student Database Management System
Handles binary file storage and indexing
"""

import struct
import os
from datetime import datetime
from pathlib import Path
from btree import BTree


SAMPLE_STUDENTS = [
    (1001, "Nguyễn Văn An", "M", "2003-01-14", 3.65, "0912001101"),
    (1002, "Trần Thị Bích", "F", "2003-02-21", 3.80, "0912001102"),
    (1003, "Lê Đức Bảo", "M", "2002-11-03", 3.25, "0912001103"),
    (1004, "Phạm Thu Hà", "F", "2003-06-09", 3.95, "0912001104"),
    (1005, "Võ Minh Khoa", "M", "2003-04-17", 2.98, "0912001105"),
    (1006, "Đặng Ngọc Mai", "F", "2002-12-25", 3.40, "0912001106"),
    (1007, "Hoàng Gia Huy", "M", "2003-09-12", 3.10, "0912001107"),
    (1008, "Bùi Khánh Linh", "F", "2003-05-30", 3.72, "0912001108"),
    (1009, "Đoàn Quốc Việt", "M", "2002-10-11", 2.85, "0912001109"),
    (1010, "Phan Mỹ Tiên", "F", "2003-08-04", 3.55, "0912001110"),
    (1011, "Trương Đức Minh", "M", "2003-03-27", 3.88, "0912001111"),
    (1012, "Ngô Thanh Tâm", "F", "2002-07-19", 3.18, "0912001112"),
    (1013, "Mai Quốc Anh", "M", "2001-09-02", 2.75, "0912001113"),
    (1014, "Huỳnh Bảo Châu", "F", "2003-11-21", 3.91, "0912001114"),
    (1015, "Phùng Gia Bảo", "M", "2002-04-16", 3.32, "0912001115"),
    (1016, "Nguyễn Kim Ngân", "F", "2003-01-05", 3.67, "0912001116"),
    (1017, "Trần Duy Khang", "M", "2002-08-13", 2.99, "0912001117"),
    (1018, "Bùi Thu Trang", "F", "2001-12-28", 3.44, "0912001118"),
    (1019, "Lê Minh Trí", "M", "2003-07-07", 3.08, "0912001119"),
    (1020, "Võ Ngọc Hân", "F", "2002-02-14", 3.84, "0912001120"),
    (1021, "Đỗ Thanh Sơn", "M", "2003-10-09", 2.61, "0912001121"),
    (1022, "Đặng Phương Vy", "F", "2002-05-23", 3.73, "0912001122"),
    (1023, "Hoàng Minh Tuấn", "M", "2001-11-30", 3.52, "0912001123"),
    (1024, "Phan Tú Linh", "F", "2003-06-18", 3.27, "0912001124"),
    (1025, "Nguyễn Quang Vinh", "M", "2002-03-01", 3.46, "0912001125"),
    (1026, "Trần Bảo Yến", "F", "2001-08-26", 3.11, "0912001126"),
    (1027, "Đoàn Gia Phúc", "M", "2003-12-12", 2.88, "0912001127"),
    (1028, "Vũ Nhật Lệ", "F", "2002-09-15", 3.96, "0912001128"),
]

SAMPLE_MIN_ROWS = 28


def normalize_dob(value):
    """Normalize DOB into yyyy-mm-dd for storage consistency."""
    raw = (value or "").strip()
    if not raw:
        return raw

    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


class Student:
    """Student record class"""
    def __init__(self, student_id, name, gender, date_of_birth, gpa, phone):
        self.student_id = student_id
        self.name = name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.gpa = gpa
        self.phone = phone

    def to_bytes(self):
        """Convert student to bytes"""
        # Format: student_id (4 bytes), name (50 bytes), gender (1 byte),
        # date_of_birth (10 bytes), gpa (4 bytes float), phone (15 bytes)
        name_bytes = self.name.encode('utf-8')[:50].ljust(50, b'\x00')
        gender_bytes = self.gender.encode('utf-8')[:1]
        dob_bytes = self.date_of_birth.encode('utf-8')[:10].ljust(10, b'\x00')
        phone_bytes = self.phone.encode('utf-8')[:15].ljust(15, b'\x00')
        
        return (struct.pack('I', self.student_id) +
                name_bytes +
                gender_bytes +
                dob_bytes +
                struct.pack('f', self.gpa) +
                phone_bytes)

    @staticmethod
    def from_bytes(data):
        """Convert bytes to student"""
        offset = 0
        student_id = struct.unpack('I', data[offset:offset+4])[0]
        offset += 4
        name = data[offset:offset+50].rstrip(b'\x00').decode('utf-8')
        offset += 50
        gender = data[offset:offset+1].decode('utf-8', errors='ignore')
        offset += 1
        date_of_birth = data[offset:offset+10].rstrip(b'\x00').decode('utf-8')
        offset += 10
        gpa = struct.unpack('f', data[offset:offset+4])[0]
        offset += 4
        phone = data[offset:offset+15].rstrip(b'\x00').decode('utf-8')
        
        return Student(student_id, name, gender, date_of_birth, gpa, phone)

    def __repr__(self):
        return f"Student({self.student_id}, {self.name}, {self.gender}, {self.date_of_birth}, {self.gpa}, {self.phone})"


class StudentDatabase:
    """Student database with B-Tree indexing"""
    
    RECORD_SIZE = 4 + 50 + 1 + 10 + 4 + 15  # 84 bytes per record
    
    def __init__(self, db_file="students.db", auto_seed=True):
        default_dir = Path(__file__).resolve().parent
        db_path = Path(db_file)
        if not db_path.is_absolute():
            db_path = default_dir / db_path

        self.db_file = str(db_path)
        self.students = {}  # In-memory cache: {student_id: Student}
        self.id_btree = BTree(order=3)  # B-Tree index by student ID
        self.name_btree = BTree(order=3)  # B-Tree index by (name, student_id)
        self.load_database()
        if auto_seed:
            self.ensure_sample_coverage()

    def load_database(self):
        """Load database from binary files"""
        migrated = False
        if os.path.exists(self.db_file):
            with open(self.db_file, 'rb') as f:
                while True:
                    data = f.read(self.RECORD_SIZE)
                    if not data or len(data) < self.RECORD_SIZE:
                        break
                    student = Student.from_bytes(data)
                    new_dob = normalize_dob(student.date_of_birth)
                    if new_dob != student.date_of_birth:
                        student.date_of_birth = new_dob
                        migrated = True
                    self.students[student.student_id] = student
        self._rebuild_indexes()
        self._assert_indexes_valid()
        if migrated:
            self.save_database()

    def add_student(self, student):
        """Add a new student to database"""
        if student.student_id in self.students:
            return False, "Mã sinh viên đã tồn tại"
        
        self.students[student.student_id] = student
        self._rebuild_indexes()
        self._assert_indexes_valid()
        self.save_database()
        return True, "Thêm sinh viên thành công"

    def delete_student(self, student_id):
        """Delete a student from database"""
        if student_id not in self.students:
            return False, "Không tìm thấy sinh viên"

        del self.students[student_id]
        self._rebuild_indexes()
        self._assert_indexes_valid()
        self.save_database()
        return True, "Xóa sinh viên thành công"

    def search_by_id(self, student_id):
        """Search student by ID"""
        result = self.id_btree.search(student_id)
        if result is not None:
            return self.students.get(result)
        return None

    def search_by_name(self, name):
        """Search student by name (partial match)"""
        keyword = name.lower()
        matches = [student for student in self.students.values() if keyword in student.name.lower()]
        return sorted(matches, key=lambda s: s.student_id)

    def get_all_students(self):
        """Get all students sorted by ID"""
        return sorted(self.students.values(), key=lambda x: x.student_id)

    def save_database(self):
        """Save database to binary file"""
        with open(self.db_file, 'wb') as f:
            for student in self.get_all_students():
                f.write(student.to_bytes())

    def get_id_index_info(self):
        """Get B-Tree index info for displaying"""
        return self.id_btree.get_all_entries()

    def get_name_index_info(self):
        """Get B-Tree index info for displaying"""
        return self.name_btree.get_all_entries()

    def get_id_index_levels(self):
        """Get B-Tree levels for ID index visualization"""
        return self.id_btree.get_level_keys()

    def get_name_index_levels(self):
        """Get B-Tree levels for Name index visualization"""
        return self.name_btree.get_level_keys()

    def _sample_students(self):
        """Build sample student objects from static constants"""
        return [Student(*raw) for raw in SAMPLE_STUDENTS]

    def ensure_sample_coverage(self):
        """Ensure demo database has enough diverse rows for visualization"""
        changed = False

        # Keep canonical sample profiles (name with accents + yyyy-mm-dd DOB).
        for sample in self._sample_students():
            existing = self.students.get(sample.student_id)
            if existing is None:
                self.students[sample.student_id] = sample
                changed = True
                continue

            if (
                existing.name != sample.name
                or existing.gender != sample.gender
                or normalize_dob(existing.date_of_birth) != sample.date_of_birth
                or existing.phone != sample.phone
            ):
                existing.name = sample.name
                existing.gender = sample.gender
                existing.date_of_birth = sample.date_of_birth
                existing.phone = sample.phone
                changed = True

        if len(self.students) < SAMPLE_MIN_ROWS:
            changed = True

        if changed:
            self._rebuild_indexes()
            self._assert_indexes_valid()
            self.save_database()

    def _rebuild_indexes(self):
        """Rebuild both indexes from the source-of-truth student table."""
        self.id_btree = BTree(order=3)
        self.name_btree = BTree(order=3)

        for student in self.get_all_students():
            self.id_btree.insert(student.student_id, student.student_id)
            self.name_btree.insert((student.name.lower(), student.student_id), student.student_id)

    def _assert_indexes_valid(self):
        """Raise an error if index structures violate B-Tree invariants."""
        status = self.validate_indexes()
        if not status["id"]["ok"]:
            raise RuntimeError(f"ID index invalid: {status['id']['message']}")
        if not status["name"]["ok"]:
            raise RuntimeError(f"Name index invalid: {status['name']['message']}")

    def validate_indexes(self):
        """Validate both B-Tree indexes"""
        id_ok, id_msg = self.id_btree.validate()
        name_ok, name_msg = self.name_btree.validate()
        return {
            "id": {"ok": id_ok, "message": id_msg},
            "name": {"ok": name_ok, "message": name_msg},
        }
