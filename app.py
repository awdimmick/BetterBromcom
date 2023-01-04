import json

from flask import Flask, session, render_template, redirect, url_for, abort, request, flash
from BromcomConnector.bromcom_connect import BromcomConnector, BromcomAuthError
from BromcomConnector.settings import Settings
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)


def authenticated():
    print(f"Authentication check: {'odata_creds' in session}")
    return 'odata_creds' in session


def logout():
    if 'odata_creds' in session:
        del session['odata_creds']


def get_bromcom_connector():
    username = session['odata_creds']['username']
    password = session['odata_creds']['password']
    return BromcomConnector(username, password)


@app.route('/')
def index():  # put application's code here

    if not authenticated():
        abort(401)

    return render_template('start.html')


@app.route('/class/<collection_id>')
def show_collection_page(collection_id):

    if not authenticated():
        abort(401)

    try:
        return render_template("class_group.html", c=get_bromcom_connector().get_collection_by_id(collection_id))
    except IndexError as e:
        print(e)
        return abort(404)

    except KeyError as e:
        print(e)
        return abort(404)


@app.route('/class')
def show_collection_page_by_description():

    if not authenticated():
        abort(401)

    try:
        group_name = request.args.get('name').upper()

        if "/" in group_name:
            name_parts = group_name.split("/")
            group_name = name_parts[0].upper() + "/" + name_parts[1].title()

        return render_template("class_group.html", c=get_bromcom_connector().get_collection_by_description(group_name))

    except IndexError as e:
        print(e)
        return abort(404)

    except KeyError as e:
        print(e)
        return abort(404)


@app.route('/api/classgroup/<int:id>')
def api_get_classgroup_by_id(id):

    if not authenticated():
        abort(401)


    try:
        c = get_bromcom_connector().get_collection_by_id(id)
        c.load_behaviours_into_students()
        # b_events = c.get_behaviour_events()

        collection_data = {
            'id':id,
            'name': c.name,
            'description': c.description,
            'type': c.type_description,
            'students': []
        }
        for s in c.get_students():
            negative_points_total = 0
            positive_points_total = 0

            student_data = {
                'id':s.id,
                'display_name':s.display_name,
                'last_name': s.last_name,
                'tutor_group': s.tutor_group,
                'house': s.house,
                'year_group': s.year_group,
                'behaviours': [],
                'sen': s.sen,
                'sen_provision': s.sen_provision,
                'tilt': s.tilt,
            }

            for b in s.get_behaviour_events():
                student_data['behaviours'].append({
                    'id': b.id,
                    'name': b.name,
                    'type': b.type,
                    'adjustment': b.adjustment,
                    'description': b.description,
                    'date': b.date,
                    'comment': b.comment,
                    'staff_code': b.staff_code,
                    'subject': b.subject
                })

                if b.type == "Positive":
                    positive_points_total += int(b.adjustment)
                elif b.type == "Negative":
                    negative_points_total += int(b.adjustment)

            student_data['behaviour_count'] = len(student_data['behaviours'])
            student_data['positive_points'] = positive_points_total
            student_data['negative_points'] = negative_points_total

            collection_data['students'].append(student_data)

        return json.dumps(collection_data)

    except IndexError as e:
        print(e)
        return abort(404)

    except KeyError as e:
        print(e)
        return abort(404)


@app.route('/login', methods=['GET', 'POST'])
def process_login():

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        try:
            school_id = request.form['school_id']
            api_key = request.form['key']
            BromcomConnector(school_id, api_key)
            session['odata_creds'] = {'username': school_id, 'password': api_key}
            print("LOG: Authenticated with Bromcom successfully.")
            return render_template("start.html")

        except BromcomAuthError:
            print("ERROR: Unable to authenticate connection to Bromcom. Invalid credentials supplied.")
            if 'odata_creds' in session:
                del session['odata_creds']
            flash("Unable to connect to Bromcom. Invalid credentials provided.")
            return render_template("login.html")


@app.route('/logout')
def process_logout():
    logout()
    return render_template("login.html")


@app.errorhandler(401)
def not_authenticated(e):
    return render_template("login.html"), 401


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8800)
