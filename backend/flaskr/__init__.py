import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# paginating the questions
def paginate_quesitons(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  # initializing CORS to enable cross-domain requests
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  # setting response headers
  @app.after_request
  def after_request(response):
    response.headers.add('Acess-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Acess-Control-Allow-Methods', 'GET, POST, DELETE')
    return response

  # GET request to get all the categories
  @app.route('/categories', methods=['GET'])
  def get_categories():
    try:
      # getting all the categories from the model and formatting them
      categories = Category.query.order_by(Category.type).all()

      if (len(categories) == 0):
        abort(404)
      
      # returning the json body
      return jsonify({
        'success': True,
        'categories': {category.id: category.type for category in categories}
      })

    except:
      abort(404)    

  # GET request & pagination for all the questions
  @app.route('/questions', methods=['GET'])
  def get_questions():
    # getting all the questions and paginating them 
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_quesitons(request, questions)

    if(len(current_questions) == 0):
      abort(404)

    categories = Category.query.order_by(Category.type).all()

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(questions),
      'categories': {category.id: category.type for category in categories},
      'current_category': None
    })

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    # attempting to get the question to delete
    try:
      question = Question.query.filter_by(id=question_id).one_or_none()

      if question is None:
        abort(404)
      
      # delete the question if it exists and redisplay the questions
      question.delete()
      questions = Question.query.order_by(Question.id).all()
      current_questions = paginate_quesitons(request, questions)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(questions)
      })
    
    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question_submission():

    # getting the json body and splitting the elemtents
    body = request.get_json()

    new_question = body.get('question')
    new_answer = body.get('answer')
    new_category = body.get('category')
    new_difficulty = body.get('difficulty')

    # attempting to add the new question
    try:
      question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
      question.insert()

      questions = Question.query.order_by(Question.id).all()
      current_questions = paginate_quesitons(request, questions)

      return jsonify({
      'success': True,
      'created': question.id,
      'questions': current_questions,
      'total_questions': len(questions)
    })

    except:
      abort(422)

  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    # getting the search term from the json body and filtering for questions containing the term
    body = request.get_json()
    search = body.get('searchTerm')
    questions = Question.query.filter(Question.question.ilike('%'+search+'%')).all()

    # paginating the questions
    current_questions = paginate_quesitons(request, questions)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(questions),
      'current_category': None
    })

  # GET request for questions in a particular category
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_categoriacal_questions(category_id):
    categoryId = Category.query.filter_by(id=category_id).one_or_none()

    if(categoryId is None):
      abort(404)

    questions = Question.query.filter_by(category=category_id).all()
    # questions = Question.query.order_by(Question.id).filter(Question.category == str(category_id)).all()

    # paginating the questions
    current_questions = paginate_quesitons(request, questions)

    return jsonify({
      'success': True,
      'current_category': category_id,
      'questions': current_questions,
      'total': len(questions)
    })

  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    # getting the json body and assigning the parts accordingly 
    body = request.get_json()

    # if there are no required fields in the response body then abort
    try:
      quiz_category = body.get('quiz_category')
      previous_questions = body.get('previous_questions')
    except: 
      abort(400)

    # if there are no required fields in the response body then abort
    # if (not all (quiz_category) or not all(previous_questions)):
    #   abort(400)

    # getting all the questions
    if (quiz_category['id'] == 0):
      questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
    else:
      questions = Question.query.filter_by(category=quiz_category['id']).all()

    # formatting all the questions then test to see if they have been asked already
    # if they haven't been asked yet, then put them in the quiz_questions list
    formatted_questions = [question.format() for question in questions]
    quiz_questions = []

    for question in formatted_questions:
      if question['id'] not in previous_questions:
        quiz_questions.append(question)

    # length of the quizzable questions
    total_quiz_questions = len(quiz_questions)

    if (total_quiz_questions > 0):
      # getting a random question
      random_question = quiz_questions[random.randrange(0, total_quiz_questions, 1)]

      # return the new random question
      return jsonify({
        'success': True,
        'question': random_question
      })

    # if there are no questions left then show the results
    else:
      return jsonify( {'question': None} )

  # error handlers (400, 404, 405, 422, 500)
  @app.errorhandler(400)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': "Bad request"
    }), 400
  
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "Not found"
    }), 404
  
  @app.errorhandler(405)
  def not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': "Method not allowed"
    }), 405  

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "Unprocessable"
    }), 422

  @app.errorhandler(500)
  def internal(error):
    return jsonify({
      'success': False,
      'error': 500,
      'message': "Internal server error"
    }), 500
  
  return app