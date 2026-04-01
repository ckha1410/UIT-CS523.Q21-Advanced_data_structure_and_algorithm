"""Web server for Student Management System.
Uses existing StudentDatabase and B-Tree logic, exposes REST APIs,
and serves a Vue (CDN) frontend from web/index.html.
"""

from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from database import Student, StudentDatabase


app = Flask(__name__, static_folder="web", static_url_path="/web")
APP_DIR = Path(__file__).resolve().parent
DB_PATH = str(APP_DIR / "students.db")
db = StudentDatabase(db_file=DB_PATH, auto_seed=True)


@app.after_request
def disable_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


def student_to_dict(student):
    return {
        "student_id": student.student_id,
        "name": student.name,
        "gender": student.gender,
        "date_of_birth": student.date_of_birth,
        "gpa": round(float(student.gpa), 2),
        "phone": student.phone,
    }


def _normalize_dob(value):
    value = (value or "").strip()
    if not value:
        return None

    dt = None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            break
        except ValueError:
            continue

    if dt is None:
        return None

    if dt.year < 1900 or dt > datetime.now():
        return None
    return dt.strftime("%Y-%m-%d")


@app.get("/")
def home():
    return send_from_directory("web", "index.html")


@app.get("/api/students")
def get_students():
    students = [student_to_dict(s) for s in db.get_all_students()]
    return jsonify(students)


@app.post("/api/students")
def add_student():
    payload = request.get_json(silent=True) or {}

    try:
        student_id = int(payload.get("student_id"))
        name = str(payload.get("name", "")).strip()
        gender = str(payload.get("gender", "")).strip().upper()
        date_of_birth = str(payload.get("date_of_birth", "")).strip()
        gpa = float(payload.get("gpa"))
        phone = str(payload.get("phone", "")).strip()
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Dữ liệu nhập không hợp lệ"}), 400

    if student_id <= 0:
        return jsonify({"ok": False, "message": "Mã sinh viên phải là số nguyên dương"}), 400

    if not name:
        return jsonify({"ok": False, "message": "Tên sinh viên không được để trống"}), 400
    if gender not in {"M", "F"}:
        return jsonify({"ok": False, "message": "Giới tính chỉ nhận M hoặc F"}), 400
    normalized_dob = _normalize_dob(date_of_birth)
    if normalized_dob is None:
        return jsonify({"ok": False, "message": "Ngày sinh không hợp lệ (định dạng yyyy-mm-dd)"}), 400
    if gpa < 0.0 or gpa > 4.0:
        return jsonify({"ok": False, "message": "GPA phải nằm trong khoảng 0.0 đến 4.0"}), 400
    if not phone:
        return jsonify({"ok": False, "message": "Số điện thoại không được để trống"}), 400

    ok, message = db.add_student(
        Student(
            student_id=student_id,
            name=name,
            gender=gender,
            date_of_birth=normalized_dob,
            gpa=gpa,
            phone=phone,
        )
    )
    if ok:
        return jsonify({"ok": True, "message": f"Thêm sinh viên {student_id} thành công"}), 200
    return jsonify({"ok": False, "message": message}), 409


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    if student_id <= 0:
        return jsonify({"ok": False, "message": "Mã sinh viên phải là số nguyên dương"}), 400

    ok, message = db.delete_student(student_id)
    if ok:
        return jsonify({"ok": True, "message": f"Xóa sinh viên {student_id} thành công"}), 200
    return jsonify({"ok": False, "message": message}), 404


@app.get("/api/search/id/<int:student_id>")
def search_by_id(student_id):
    if student_id <= 0:
        return jsonify({"ok": False, "message": "Mã sinh viên phải là số nguyên dương", "result": None}), 400

    student = db.search_by_id(student_id)
    if student is None:
        return jsonify({"ok": True, "message": f"Không tìm thấy sinh viên có mã {student_id}", "result": None})
    return jsonify({"ok": True, "message": f"Đã tìm thấy sinh viên có mã {student_id}. Thông tin sinh viên được hiển thị như trên!", "result": student_to_dict(student)})


@app.get("/api/search/name")
def search_by_name():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"ok": False, "message": "Vui lòng nhập từ khóa tên để tìm kiếm", "result": []}), 400

    result = [student_to_dict(s) for s in db.search_by_name(keyword)]
    if not result:
        return jsonify({"ok": True, "message": f"Không tìm thấy sinh viên nào với từ khóa '{keyword}'", "result": []})
    return jsonify({"ok": True, "message": f"Tìm thấy {len(result)} sinh viên với từ khóa '{keyword}'", "result": result})


@app.get("/api/index/id")
def id_index():
    return jsonify(
        {
            "entries": db.get_id_index_info(),
            "levels": db.get_id_index_levels(),
            "tree": db.id_btree.export_tree(),
        }
    )


@app.get("/api/index/name")
def name_index():
    return jsonify(
        {
            "entries": db.get_name_index_info(),
            "levels": db.get_name_index_levels(),
            "tree": db.name_btree.export_tree(),
        }
    )


@app.get("/api/self-check")
def self_check():
    status = db.validate_indexes()
    return jsonify(status)


@app.get("/api/debug/runtime")
def runtime_debug():
    # Runtime visibility to diagnose mismatched environments quickly.
    all_students = db.get_all_students()
    return jsonify(
        {
            "db_file": db.db_file,
            "total_students": len(db.students),
            "first_student": student_to_dict(all_students[0]) if all_students else None,
            "cwd": str(Path.cwd()),
            "app_dir": str(APP_DIR),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
