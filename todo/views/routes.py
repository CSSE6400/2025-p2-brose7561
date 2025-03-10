from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta

 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})



@api.route('/todos', methods=['GET'])
def get_todos():
    completed_filter = request.args.get('completed', type=str)
    window = request.args.get('window', type=int)
    
    if completed_filter is not None:
        completed_filter = completed_filter.lower() == 'true'
        todos = Todo.query.filter_by(completed=completed_filter).all()
    else:
        todos = Todo.query.all()

    if window is not None:
        now = datetime.now()
        cutoff = now + timedelta(days=window)
        todos = [todo for todo in todos if todo.deadline_at <= cutoff]

    result = [todo.to_dict() for todo in todos]
    return jsonify(result)



@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())


@api.route('/todos', methods=['POST'])
def create_todo():
    todo_data = request.get_json()

    if not todo_data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    expected_fields = {'title', 'description', 'completed', 'deadline_at'}
    provided_fields = set(todo_data.keys())

    extra_fields = provided_fields - expected_fields
    if extra_fields:
        return jsonify({'error': f"Unexpected fields: {', '.join(extra_fields)}"}), 400

    todo = Todo(
        title=todo_data.get('title'),
        description=todo_data.get('description'),
        completed=todo_data.get('completed', False),
    )

    if 'deadline_at' in todo_data:
        todo.deadline_at = datetime.fromisoformat(todo_data.get('deadline_at'))

    db.session.add(todo)
    db.session.commit()

    return jsonify(todo.to_dict()), 201



@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo_data = request.get_json()

    if 'id' in todo_data and todo_data['id'] != todo_id:
        return jsonify({'error': 'Cannot change ID'}), 400

    # Check for extra fields in the request
    valid_fields = {'title', 'description', 'completed', 'deadline_at'}
    extra_fields = set(todo_data.keys()) - valid_fields
    if extra_fields:
        return jsonify({'error': f"Invalid fields: {', '.join(extra_fields)}"}), 400

    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    todo.title = todo_data.get('title', todo.title)
    todo.description = todo_data.get('description', todo.description)
    todo.completed = todo_data.get('completed', todo.completed)
    todo.deadline_at = todo_data.get('deadline_at', todo.deadline_at)

    db.session.commit()

    return jsonify(todo.to_dict()), 200




@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200

    db.session.delete(todo)
    db.session.commit()

    return jsonify(todo.to_dict()), 200

 
