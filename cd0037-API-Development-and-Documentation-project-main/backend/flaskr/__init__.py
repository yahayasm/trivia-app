from nis import cat
import os
from sre_parse import CATEGORIES
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(response, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start * QUESTIONS_PER_PAGE
    
    questions = [question.format() for question in selection]
    current_question = questions[start:end]
    
    return current_question

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_reguest
    def after_request(response):
        response.header.add('Access-Control-Allow-Headers','Content-Type, Authorization, true')
        response.header.add('Access-Control-Allow-Methods','GET, PUT, POST, DELETE, OPTIONS')
        
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.router('/categories', methods=['GET'])
    def retrieve_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = paginate_questions(request, selection)
        if len(categories) == 0:
            abort(404)
        
        return jsonify(
            {
                "success": True,
                "categories": categories,
                "total_categories": len(Category.query.all()),
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=["GET"])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        categories = Category.query.order_by(Category.id).all()
        current_question = paginate_questions(request, selection)
        
        if len(current_question) == 0:
            abort(404)
        
        return jsonify({
            'success': True,
            'question': current_question,
            'Total_question': len(current_question),
            'catetories': {
                Category.id: Category.type for category in categories
                },
            'current_category': None
        })
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<question_id>", methods =['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            
            if question is None:
                abort(404)
                
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            
            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "Questions": current_questions,
                    "total_question": len(Question.query.all()),
                }
            )
            
        except:
            abort(422)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods = ['POST'])
    def post_question():
        body = request.get_json()
        
        new_question = body.get('question')
        new_answer = body.get('answer')
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')
           
        try:            
            question = Question(
                qustion = new_question, 
                answer= new_answer, 
                difficulty=new_difficulty, 
                category=new_category)
            question.insert()
            
            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "Questions": current_question,
                    "total_questons": len(Question.query.all()),
                }
            )
            
        except:
            abort(422)
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions')
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm')
        
        try:
            if search_term is None:
                abort(404)
                        
            search_results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
            
            return jsonify(
                {
                    'success': True,
                    'questions': [question.format() for question in search_results],
                    'total_question': len(search_results),
                    'current_category': None
                }
            )
        except:
            abort(422)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:category_id>/questions", methods=['GET'])
    def retrieve_questions_by_category(category_id):
        try:
            questions_per_cat = Question.query.filter(Question.categoy == category_id).one_or_none()
            
            if questions_per_cat is None:
                abort(404)
                
            return jsonify(
                {
                    'success': True,
                    'questions': [question.format() for question in questions_per_cat],
                    'total_question': len(questions_per_cat),
                    'current_category': category_id
                }
            )
        except:
            abort(404)
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            category = body.get('quiz_category')
            previous_questions = body.get('revious_questions')
            
            if category and previous_questions is None:
                abort(422)
                          
            if category['type'] == 'click':
                available_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(category = category['id'].filter(Question.id.notin_((previous_questions)))).all()
                
            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None
            
            return jsonify(
                {
                    'success': True,
                    'question': new_question
                }
            )
            
        except:
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(eror):
        return jsonify(
            {
                'success': False,
                'error': 404,
                'message': 'resources not found'
            }),404
        
    @app.errorhandler(422)
    def not_found(eror):
        return jsonify(
            {
                'success': False,
                'error': 422,
                'message': 'unprocessable'
            }),422
        
    @app.errorhandler(400)
    def not_found(eror):
        return jsonify(
            {
                'success': False,
                'error': 400,
                'message': 'bad request'
         }),400
        
               
    return app