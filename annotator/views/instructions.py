from itertools import groupby

from flask import flash, render_template, request
from flask_login import login_required, current_user

from annotator.app import app
from annotator.extensions import db
from annotator.models import Dataset, LabelEvent, Problem, ProblemLabel, User
from annotator.utils import assert_rights_to_problem

@app.route('/<uuid:problem_id>/instructions')
@login_required

def instructions(problem_id):

    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)

    return render_template(
        'instructions.html',
		problem=problem
    )
