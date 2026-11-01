from flask import current_app, render_template, Blueprint, jsonify, flash, url_for, redirect,request


from peewee import JOIN, fn

from .. models import User, Animal, Image, Admin
from flask_login import current_user, login_user, logout_user
from .. forms import LoginForm
from .. config import Config
from .. database import db

app1 = Blueprint("home", __name__)
# app1.config['SECRET_KEY'] = 'some-super-secret-string-here'

@app1.route('/')
def index():
    animals = (
        Animal
        .select(
            Animal.id,
            Animal.name,
            Animal.breed,
            Animal.gender,
            Image.url.alias("primary_image")
        )
        .join(
            Image,
            JOIN.LEFT_OUTER,
            on=(
                (Image.animal == Animal.id) &
                (Image.is_primary == True)
            )
        )
        .order_by(fn.Random())
        .limit(1)
        .dicts()
    )
    
    featured_animal_list = []

    for animal in animals:
        featured_animal_list.append(animal)

    return render_template('index.html', animals=featured_animal_list), 200

@app1.route('/adopt')
def adopt():
    animals = (
        Animal
        .select(
            Animal.id,
            Animal.name,
            Animal.breed,
            Animal.gender,
            Image.url.alias("primary_image")
        )
        .join(
            Image,
            JOIN.LEFT_OUTER,
            on=(
                (Image.animal == Animal.id) &
                (Image.is_primary == True)
            )
        )
        .dicts()
    )

    return render_template('adopt.html', animals=animals)

@app1.route('/gallery')
def gallery():
    animals = (
        Animal
        .select(
            Animal.id,
            Animal.name,
            Animal.breed,
            Animal.gender,
            Image.url.alias("primary_image")
        )
        .join(
            Image,
            JOIN.LEFT_OUTER,
            on=(
                (Image.animal == Animal.id) &
                (Image.is_primary == True)
            )
        )
        .order_by(Animal.id.desc())
        .dicts()
    )
    
    featured_animal_list = []

    for animal in animals:
        featured_animal_list.append(animal)

    return render_template('gallery.html', animals=featured_animal_list), 200


@app1.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    if request.method == 'POST':
        default_user = User.get_or_none()  # This will fail if no users exist; replace with proper user selection
        if not default_user:
            flash("No users available to assign as owner.")
            return redirect(url_for('home.add_pet'))
        
        try:
            int(request.form.get("age"))
        except ValueError:
            flash("Age must be a number")
            return redirect(url_for('home.add_pet'))
        with db.atomic():
            pet = Animal(
                owner=default_user,
                name=request.form.get("name"),
                species=request.form.get("species"),
                breed=request.form.get("breed"),
                gender=request.form.get("gender"),
                age=int(request.form.get("age")),
                size=request.form.get("size"),
                color=request.form.get("color"),
                house_trained=request.form.get("house_trained"),
                description=request.form.get("description")
            )
            pet.save() 
            image = Image(
                url=request.form.get("url"),
                animal=pet,
                is_primary = True
            )
            image.save()
        
        flash(f"Pet successfully added")
        return redirect(url_for('home.add_pet')), 302
    else:
        return render_template('add_pet.html'), 200

@app1.route('/user_info')
def view_users():
    users_to_view = User.select()
    user_list = []

    for user in users_to_view:
        user_list.append(user.to_dict())

    return jsonify(user_list), 200

@app1.route('/pet_info')
def view_pets():
    animals_to_view = Animal.select()
    animal_list = []

    for animal in animals_to_view:
        animal_list.append(animal.to_dict())

    return jsonify(animal_list), 200
    
    
@app1.route('/image_info')
def view_images():
    images_to_view = Image.select()
    image_list = []

    for image in images_to_view:
        image_list.append(image.to_dict())

    return jsonify(image_list), 200


@app1.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.get_or_none(Admin.username == form.username.data)
        
        if admin is None or not admin.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('home.login'))
            
        login_user(admin, remember=form.remember_me.data)
        print("authenticated!")
        return redirect(url_for('home.admin_dashboard'))
    
    return render_template('adminlogin.html', title='Sign In', form=form)

@app1.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app1.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home.index'))


@app1.route('/Forms', methods=['GET', 'POST'])
def form():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        reason = request.form.get('reason')
        message = request.form.get('message')

        if not name or not email or not phone or not reason or not message:
            return jsonify({
                "status": "error",
                "message": "All fields are required"
            }), 400

        return jsonify({
            "status": "success",
            "message": "Message Sent !"
        }), 200

    return render_template('form.html')

@app1.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        print(name, email, message)

        return jsonify({"status": "success", "message": "Message Sent !"})

    return render_template('contact.html')
