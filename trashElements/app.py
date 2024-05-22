from flask import Flask, request, jsonify
from models import db, Schedule

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    data = request.json
    schedule = Schedule(**data)
    db.session.add(schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule added successfully!'})

if __name__ == '__main__':
    app.run(debug=True)
