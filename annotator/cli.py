import re

import click
import requests
from sh import createdb, dropdb, psql

from .app import app
from .extensions import db
from .models import Dataset, Problem, ProblemLabel, User, UserProblem


@app.cli.command()
@click.argument('username')
@click.argument('password')
def add_user(username, password):
    db.session.add(User(
        username=username,
        password=password,
        is_superuser=True
    ))
    db.session.commit()
    click.echo('User %s added' % username)

@app.cli.command()
@click.argument('username')
@click.argument('password')
def normal_user(username, password):
    u = User(username=username, password=password)
    db.session.add(u)
    db.session.add(UserProblem(user=u, problem=Problem.query.get('a5145ad0-9a66-4902-8f61-94374c88e2b6')))
    db.session.add(UserProblem(user=u, problem=Problem.query.get('7401c701-4d24-470c-816e-2b89a87abd42')))
    db.session.add(UserProblem(user=u, problem=Problem.query.get('86d366ad-2ac2-45a4-b288-89c23fa3df0b')))
    db.session.commit()
    click.echo('Normal User %s added' % username)

@app.cli.command()
def import_fake_data():
    request = requests.get('https://www.gutenberg.org/files/21130/21130-0.txt')
    quotes = [
        '%s (%s)' % (x[1].strip(), x[2])
        for x in re.findall(
            '([0-9]+)\.\n\n(.+?)_(.+?)_',
            request.text.replace('\r', ''), re.DOTALL
        )
    ]

    def add_quotes(problem):
        for i, quote in enumerate(quotes):
            db.session.add(Dataset(
                table_name='gutenberg.book_of_wise_sayings',
                entity_id='quote%i' % i,
                problem=problem,
                free_text=quote
            ))

    binary_problem = Problem(
        name='Book of Wise sayings (Binary label)',
        labels=[ProblemLabel(label='Good quote', order_index=1)]
    )
    add_quotes(binary_problem)
    multi_label = Problem(
        name='Book of Wise sayings (Multi-label)',
        classification_type='multi-label',
        labels=[
            ProblemLabel(label='Motivational', order_index=1),
            ProblemLabel(label='Love', order_index=2),
            ProblemLabel(label='Inspiration', order_index=3),
            ProblemLabel(label='Relationships', order_index=4),
        ]
    )
    add_quotes(multi_label)
    multi_class = Problem(
        name='Book of Wise sayings (Multi-class)',
        classification_type='multi-class',
        labels=[
            ProblemLabel(label='Excellent', order_index=1),
            ProblemLabel(label='Good', order_index=2),
            ProblemLabel(label='Okay', order_index=3),
            ProblemLabel(label='Bad', order_index=4),
        ]
    )
    add_quotes(multi_class)

    db.session.commit()
    print('Inserted %i quotes' % len(quotes))

@app.cli.command()
def import_pride():
    import requests
    request = requests.get('https://www.gutenberg.org/files/1342/1342-0.txt')
    text_contents = max(request.text.split('***'), key=lambda x: len(x))
    paragraphs = [
        x.strip() for x in text_contents.replace('\r', '').split('\n\n')
        if x.strip()
    ]
    new_problem = Problem(
        name='Example',
        labels=[ProblemLabel(label='Example', order_index=1)],
        # supported types: binary, multi-label, multi-class
        # add more labels if using other labels.
        classification_type='binary'
    )
    for i, paragraph in enumerate(paragraphs):
        db.session.add(Dataset(
            table_name='gutenberg.pride_and_prejudice_by_jane_austen',
            entity_id='paragraph%i' % i,
            problem=new_problem,
            free_text=paragraph
        ))
    db.session.commit()

@app.cli.command()
def import_atom_ml():
    import csv
    from csv import reader
    with open('atom-risk.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        new_problem = Problem(
            name='Level 3 Risks & Controls',
            classification_type='multi-label',
            labels=[
                ProblemLabel(label='Risk Positive', order_index=1),
                ProblemLabel(label='Risk Negative', order_index=2),
                ProblemLabel(label='Control Positive', order_index=3),
                ProblemLabel(label='Control Negative', order_index=4),
                ProblemLabel(label='Not a SoI', order_index=5),
            ]
    # supported types: binary, multi-label, multi-class
    # add more labels if using other labels.
        )
        for row in csv_reader:
            db.session.add(Dataset(
                table_name=row[1],
                entity_id=row[0],
                problem=new_problem,
                free_text=row[2]
            ))
    db.session.commit()
    print('Inserted multi-label statements')

@app.cli.command()
def import_atom_mc():
    import csv
    from csv import reader
    with open('atom-risk.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        new_problem = Problem(
            name='Level 2 SoI Sentiment',
            classification_type='multi-class',
            labels=[
                ProblemLabel(label='SoI Positive', order_index=1),
                ProblemLabel(label='SoI Negative', order_index=2),
                ProblemLabel(label='Not a SoI', order_index=3),
            ]
    # supported types: binary, multi-label, multi-class
    # add more labels if using other labels.
        )
        for row in csv_reader:
            db.session.add(Dataset(
                table_name=row[1],
                entity_id=row[0],
                problem=new_problem,
                free_text=row[2]
            ))
    db.session.commit()
    print('Inserted multi-class statements')

@app.cli.command()
def import_atom_b():
    import csv
    from csv import reader
    with open('atom-risk.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)

        new_problem = Problem(
            name='Level 1 Statement of Interest',
            labels=[ProblemLabel(label='Statement of Interest', order_index=1)]
    # supported types: binary, multi-label, multi-class
    # add more labels if using other labels.
        )
        for row in csv_reader:
            db.session.add(Dataset(
                table_name=row[1],
                entity_id=row[0],
                problem=new_problem,
                free_text=row[2]
            ))
    db.session.commit()
    print('Inserted binary statements')

@app.cli.command()
def createtables():
    _createtables()


def _createtables():
    db.init_app(app)

    db.engine.execute('''CREATE EXTENSION IF NOT EXISTS "uuid-ossp";''')
    db.create_all()
    db.session.commit()

    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config('alembic.ini')
    command.stamp(alembic_cfg, 'head')


@app.cli.command()
def resetdb():
    """Create the tables."""
    import annotator.models  # noqa

    click.echo('Resetting database...')

    query = '''
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{}'
    '''.format(db.engine.url.database)
    psql('--command', query)
    dropdb('--if-exists', db.engine.url.database)
    createdb(db.engine.url.database)
    _createtables()
