from flask_sqlalchemy import SQLAlchemy

# Инициализация расширения SQLAlchemy
db = SQLAlchemy()

# Определение модели SQLAlchemy
class Schedule(db.Model):
    """
    Модель Schedule представляет собой расписание занятий.
    """
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор записи
    day_of_week = db.Column(db.String(50), nullable=False)  # День недели занятия
    time = db.Column(db.String(50), nullable=False)  # Время занятия
    week_type = db.Column(db.String(50), nullable=False)  # Тип недели (например, "под чертой" или "над чертой")
    subject = db.Column(db.String(200), nullable=False)  # Название предмета
    classroom = db.Column(db.String(50))  # Аудитория, где проходит занятие
    teacher = db.Column(db.String(100))  # Преподаватель, ведущий занятие
    lesson_type = db.Column(db.String(50))  # Тип занятия (например, лекция, семинар)
    group_name = db.Column(db.String(50))  # Название группы студентов
    start_time = db.Column(db.String(50))  # Время начала занятия
    end_time = db.Column(db.String(50))  # Время окончания занятия
    semester = db.Column(db.Integer, nullable=False)  # Номер семестра

    def __repr__(self):
        """
        Метод __repr__ определяет строковое представление объекта Schedule.
        """
        return f"Schedule('{self.day_of_week}', '{self.time}', '{self.subject}')"
