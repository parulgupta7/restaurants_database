from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import base, Restaurants, MenuItems, User
from flask import session as session_login
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

engine = create_engine('sqlite:///restaurantdatabase.db')
base.metadata.bind = engine

DataSession = sessionmaker(bind = engine)
instance = DataSession()

# Login webpage url loader
@app.route('/login')
def Login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    session_login['state'] = state
    return render_template('login.html', STATE=state)

# Other helpul functions for user
def createUser(session_login):
    user = User(name=session_login['username'], email=session_login[
                'email'], picture=session_login['picture'])
    instance.add(user)
    instance.commit()
    cust = instance.query(User).filter_by(email=session_login['email']).one()
    return cust.id

def getInfo(user_id):
    cust = instance.query(User).filter_by(id = user_id).one()
    return cust

def getID(email):
    try:
        cust = instance.query(User).filter_by(email = email).one()
        return cust.id
    except:
        return None

# Link for Google sign in or log in
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != session_login['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

        # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = session_login.get('credentials')
    stored_gplus_id = session_login.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session_login['credentials'] = credentials
    session_login['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session_login['username'] = data['name']
    session_login['picture'] = data['picture']
    session_login['email'] = data['email']

    user_id = getID(session_login['email'])
    if not user_id:
        user_id = createUser(session_login)
    session_login['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += session_login['username']
    output += '!</h1>'
    output += '<img src="'
    output += session_login['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % session_login['username'])
    print "done!"
    return output

# Sign out web page Url
@app.route('/disconnect')
def disconnect():
    credentials = session_login.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected'),401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %access_token
    h = httplib2.Http()
    result = h.request(url,'GET')[0]
    if result['status'] == '200':
        del session_login['credentials']
        del session_login['gplus_id']
        del session_login['username']
        del session_login['email']
        del session_login['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



# Homepage Url loader
@app.route('/')
@app.route('/restaurants')
def restaurants():
    restaurants = instance.query(Restaurants).all()
    if 'username' not in session_login:
        return render_template('main.html', restaurants=restaurants)
    return render_template(
        'privaterestaurant.html', restaurants=restaurants)

# Link to view menu item of particular restaurant
@app.route('/restaurants/<int:id>')
def restaurantMenu(id):
    restaurant = instance.query(Restaurants).filter_by(id=id).one()
    owner = instance.query(User).filter_by(id=restaurant.user_id).one()
    items = instance.query(MenuItems).filter_by(restaurant_id=id).all()
    if 'username' not in session_login or owner.id != session_login['user_id']:
        return render_template(
            'menu.html', items=items, owner=owner, restaurant=restaurant, id=id, s=session_login)
    return render_template(
        'privatemenu.html', restaurant=restaurant, items=items, id=id, owner=owner)


# Link to edit particular menu item in particular restaurant
@app.route('/restaurants/<int:r_id>/<int:m_id>/edit', methods=['GET', 'POST'])
def editMenu(r_id, m_id):
    if 'username' not in session_login:
        return redirect('/login')
    Item = instance.query(MenuItems).filter_by(id=m_id).one()
    restaurant = instance.query(Restaurants).filter_by(id=r_id).one()
    if session_login['user_id'] != restaurant.user_id:
        return "<script>function myFunction() {alert('Restricted Acess');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            Item.name = request.form['name']
        if request.form['course']:
            Item.course = request.form['course']
        if request.form['price']:
            Item.price = request.form['price']
        if request.form['description']:
            Item.description = request.form['description']
        instance.add(Item)
        instance.commit()
        flash("Menu item has been edited")
        return redirect(url_for('restaurantMenu', id=r_id))
    else:
        return render_template('editmenu.html', r_id=r_id, m_id=m_id, item=Item)

# Link to add new menu item to particular restaurant database
@app.route('/restaurants/<int:id>/new', methods=['GET', 'POST'])
def newMenu(id):
    if 'username' not in session_login:
        return redirect('/login')
    restaurant = instance.query(Restaurants).filter_by(id=id).one()
    if session_login['user_id'] != restaurant.user_id:
        return "<script>function myFunction() {alert('Restricted Acess');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        Item = MenuItems(name=request.form['name'], description=request.form['description'], price=request.form['price'], course=request.form['course'], restaurant_id=id, user_id=restaurant.user_id)
        instance.add(Item)
        instance.commit()
        flash("New Item has been added")
        return redirect(url_for('restaurantMenu', id=id))
    else:
        return render_template('newmenu.html', id=id)

# Link to delete Particular menu item from Particular restaurant
@app.route('/restaurants/<int:r_id>/<int:m_id>/delete',
           methods=['GET', 'POST'])
def deleteMenu(r_id, m_id):
    if 'username' not in session_login:
        return redirect('/login')
    restaurant = instance.query(Restaurants).filter_by(id=r_id).one()
    item = instance.query(MenuItems).filter_by(id=m_id).one()
    if session_login['user_id'] != restaurant.user_id:
        return "<script>function myFunction() {alert('Restricted Access');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        instance.delete(item)
        instance.commit()
        flash("Menu item has been deleted")
        return redirect(url_for('restaurantMenu', id=r_id))
    else:
        return render_template('deletemenu.html', item=item)

# Link to edit existing restaurant name in databsase
@app.route('/restaurants/<int:id>/edit', methods=['GET', 'POST'])
def editRestaurants(id):
    if 'username' not in session_login:
        return redirect('/login')
    restaurant = instance.query(Restaurants).filter_by(id=id).one()
    if restaurant.user_id != session_login['user_id']:
        return "<script>function myFunction() {alert('Restricted access');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            restaurant.name = request.form['name']
        instance.add(restaurant)
        instance.commit()
        flash("Restaurant name changed")
        return redirect(url_for('restaurants'))
    else:
        return render_template('editrestaurants.html', id=id, restaurant=restaurant)

# Link to add new restaurant to database
@app.route('/restaurants/new', methods=['GET', 'POST'])
def newRestaurant():
    if 'username' not in session_login:
        return redirect('/login')
    if request.method == 'POST':
        restaurant = Restaurants(name=request.form['name'], user_id=session_login['user_id'])
        instance.add(restaurant)
        instance.commit()
        flash("New Restaurant added")
        return redirect(url_for('restaurants'))
    else:
        return render_template('newrestaurant.html')

# Link to delete existing restaurant in databsase
@app.route('/restaurants/<int:id>/delete',
           methods=['GET', 'POST'])
def deleteRestaurant(id):
    item = instance.query(Restaurants).filter_by(id=id).one()
    if 'username' not in session_login:
        return redirect('/login')
    if item.user_id != session_login['user_id']:
        return "<script>function myFunction() {alert('Restricted access');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        instance.delete(item)
        instance.commit()
        flash("Restaurant deleted")
        return redirect(url_for('restaurants'))
    else:
        return render_template('deleterestaurants.html', id=id, item=item)

# Fuctions to create Json files from database
@app.route('/JSON')
def JSON():
    List = instance.query(Restaurants).all()
    return jsonify(Restaurants=[x.serialize for x in List])

@app.route('/restaurants/<int:r_id>/JSON')
def MenuJSON(r_id):
    items = instance.query(MenuItems).filter_by(
        restaurant_id=r_id).all()
    return jsonify(MenuItems=[x.serialize for x in items])

@app.route('/restaurants/<int:r_id>/menu/<int:m_id>/JSON')
def menuItemJSON(r_id, m_id):
    menu = instance.query(MenuItems).filter_by(id=m_id, restaurant_id=r_id).one()
    return jsonify(MenuItems=menu.serialize)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)