from dataclasses import dataclass


@dataclass
class Student:
    full_name: str
    home_phone: str
    father_cell: str
    father_name: str
    mother_cell: str
    mother_name: str
    primary_email: str
    class_name: str
    teacher_id: str = None
    teacher_full_name: str = None


@dataclass
class Attendance:
    date: str
    student_name: str
    class_name: str
    status: str
    mother_info: str = None
    father_info: str = None
    primary_email: str = None


@dataclass
class Total:
    date: str
    class_name: str
    present_count: str
    informed_absent_count: str
    absent_count: str
