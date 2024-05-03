from flask_sqlalchemy import SQLAlchemy

# Инициализация расширения SQLAlchemy
db = SQLAlchemy()

# Определение модели SQLAlchemy
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    week_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    classroom = db.Column(db.String(50))
    teacher = db.Column(db.String(100))
    lesson_type = db.Column(db.String(50))
    group_name = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    semester = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Schedule('{self.day_of_week}', '{self.time}', '{self.subject}')"
