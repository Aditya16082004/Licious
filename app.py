from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Aditya@827'
app.config['MYSQL_DB'] = 'project'
mysql = MySQL(app)

# Function to fetch products from MySQL
def fetch_products():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return products

def fetch_recipes():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT recipe_id, title, description FROM recipes")
    recipes = cur.fetchall()
    cur.close()
    return recipes


# Function to add a new recipe to MySQL
def add_recipe(title, description, ingredients, instructions):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO recipes (title, description, ingredients, instructions)
        VALUES (%s, %s, %s, %s)
    """, (title, description, ingredients, instructions))
    mysql.connection.commit()
    cur.close()

# Function to update a recipe in MySQL
def update_recipe(recipe_id, title, description, ingredients, instructions):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE recipes
        SET title = %s, description = %s, ingredients = %s, instructions = %s
        WHERE recipe_id = %s
    """, (title, description, ingredients, instructions, recipe_id))
    mysql.connection.commit()
    cur.close()

# Function to delete a recipe from MySQL
def delete_recipe(recipe_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM recipes WHERE recipe_id = %s", (recipe_id,))
    mysql.connection.commit()
    cur.close()
# Function to fetch product details from MySQL
def fetch_product(product_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    return product

# Function to store order details in MySQL
def store_order(customer_id, items, total_price, delivery_address):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO orders (customer_id, items, total_price, delivery_address) VALUES (%s, %s, %s, %s)",
                (customer_id, str(items), total_price, delivery_address))
    mysql.connection.commit()
    cur.close()

# Function to fetch recipes from MySQL
def fetch_recipes():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM recipes")
    recipes = cur.fetchall()
    cur.close()
    return recipes

def get_product_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]
    cur.close()
    return count

def get_recipe_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM recipes")
    count = cur.fetchone()[0]
    cur.close()
    return count

def get_user_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM accounts")
    count = cur.fetchone()[0]
    cur.close()
    return count

def get_order_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM orders")
    count = cur.fetchone()[0]
    cur.close()
    return count


@app.route('/')
def home():
    if 'loggedin' in session:
        products = fetch_products()
        return render_template('home.html', products=products)
    return redirect(url_for('login'))

@app.route('/recipes')
def recipes():
    recipes_list = fetch_recipes()  # Call the function to fetch recipes
    return render_template('recipes.html', recipes=recipes_list)

@app.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM recipes WHERE recipe_id = %s", (recipe_id,))
    recipe = cur.fetchone()
    cur.close()
    return render_template('recipe_details.html', recipe=recipe)

@app.route('/admin/recipe')
def admin_recipe():
    recipes_list = fetch_recipes()
    return render_template('admin_recipe.html', recipes=recipes_list)



@app.route('/admin/add_recipe', methods=['GET', 'POST'])
def admin_add_recipe():
    if 'loggedin' in session and session.get('is_admin'):
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            ingredients = request.form['ingredients']
            instructions = request.form['instructions']
            
            add_recipe(title, description, ingredients, instructions)
            
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('admin_recipes'))  # Redirect to admin recipes page after adding

        return render_template('admin_add_recipe.html')  # Render the add recipe form template

    return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in or not admin


@app.route('/admin/update_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def admin_update_recipe(recipe_id):
    if 'loggedin' in session and session.get('is_admin'):
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            ingredients = request.form['ingredients']
            instructions = request.form['instructions']
            
            update_recipe(recipe_id, title, description, ingredients, instructions)
            
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('admin_recipes'))  # Redirect to admin recipes page after updating
        
        # Fetch the recipe details using the existing function
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM recipes WHERE recipe_id = %s", (recipe_id,))
        recipe = cur.fetchone()
        cur.close()
        
        return render_template('admin_update_recipe.html', recipe=recipe)  # Render the update recipe form template

    return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in or not admin

@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
def admin_delete_recipe(recipe_id):
    if 'loggedin' in session and session.get('is_admin'):
        delete_recipe(recipe_id)
        flash('Recipe deleted successfully!', 'success')
    return redirect(url_for('admin_recipes'))  # Redirect to admin recipes page after deleting


# Shopping Cart Routes and Functions
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_price = sum(float(item['quantity']) * float(item['product'].get('price', 0)) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart_items = session.get('cart', [])
    product = fetch_product(product_id)
    
    existing_item = next((item for item in cart_items if item['product']['product_id'] == product_id), None)
    if existing_item:
        existing_item['quantity'] += 1
    else:
        cart_items.append({'product': product, 'quantity': 1})
    
    session['cart'] = cart_items
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_items = session.get('cart', [])
    for index, item in enumerate(cart_items):
        if item['product']['product_id'] == product_id:
            cart_items.pop(index)
            break

    session['cart'] = cart_items
    flash('Item removed from cart successfully.', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items = session.get('cart', [])
    total_price = sum(item['quantity'] * float(item['product'].get('price', 0)) for item in cart_items)

    if request.method == 'POST':
        customer_name = request.form.get('name')
        customer_email = request.form.get('email')
        customer_address = request.form.get('address')
        
        payment_successful = True  # Replace with actual payment validation logic
        
        if payment_successful:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO customers (name, email, address) VALUES (%s, %s, %s)",
                        (customer_name, customer_email, customer_address))
            mysql.connection.commit()
            customer_id = cur.lastrowid
            cur.close()

            store_order(customer_id, cart_items, total_price, customer_address)
            
            session.pop('cart', None)
            flash('Order placed successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Payment failed. Please try again.', 'error')

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

# Chatbot Routes and Functions
@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_message = str(request.form['messageText'])
    bot_response = chat.send_message(user_message)

    if "ingredients" not in bot_response.text.lower():
        new_response = bot_response.text + "\n**Ingredients are not currently included, but I'm still learning!**"
    else:
        new_response = bot_response.text

    return jsonify({'status': 'OK', 'answer': new_response})

# User Authentication Routes and Functions
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully!'
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        organisation = request.form['organisation']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        postalcode = request.form['postalcode']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            cursor.execute('INSERT INTO accounts (username, password, email, organisation, address, city, state, country, postalcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (username, password, email, organisation, address, city, state, country, postalcode))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

@app.route("/display")
def display():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template("display.html", account=account)
    return redirect(url_for('login'))

@app.route("/update", methods=['GET', 'POST'])
def update():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            organisation = request.form['organisation']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            country = request.form['country']
            postalcode = request.form['postalcode']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            else:
                cursor.execute('UPDATE accounts SET username = %s, password = %s, email = %s, organisation = %s, address = %s, city = %s, state = %s, country = %s, postalcode = %s WHERE id = %s',
                               (username, password, email, organisation, address, city, state, country, postalcode, session['id']))
                mysql.connection.commit()
                msg = 'You have successfully updated!'
        elif request.method == 'POST':
            msg = 'Please fill out the form!'
        return render_template("update.html", msg=msg)
    return redirect(url_for('login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s AND is_admin = TRUE', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Incorrect username / password or not an admin!'
    return render_template('admin_login.html', msg=msg)

@app.route('/admin/logout')
def admin_logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'loggedin' in session and session.get('is_admin'):
        # Fetch statistics data
        product_count = get_product_count()
        recipe_count = get_recipe_count()
        user_count = get_user_count()
        order_count = get_order_count()
        
        return render_template('admin_dashboard.html',
                               product_count=product_count,
                               recipe_count=recipe_count,
                               user_count=user_count,
                               order_count=order_count)
    return redirect(url_for('admin_login'))


@app.route('/admin/products')
def admin_products():
    if 'loggedin' in session and session.get('is_admin'):
        products = fetch_products()
        return render_template('admin_products.html', products=products)
    return redirect(url_for('admin_login'))

# Flask Route for adding a product
@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if 'loggedin' in session and session.get('is_admin'):
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            category = request.form['category']
            dietary_preference = request.form['dietary_preference']
            image_url = request.form['image_url']
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO products (name, description, price, category, dietary_preference, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
                        (name, description, price, category, dietary_preference, image_url))
            mysql.connection.commit()
            cur.close()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))  # Redirect to admin products page after adding

        return render_template('admin_add_product.html')  # Render the add product form template

    return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in or not admin


@app.route('/admin/recent_orders')
def admin_recent_orders():
    if 'loggedin' in session and session.get('is_admin'):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                id AS order_id,
                customer_id,
                items,
                total_price,
                delivery_address,
                created_at 
            FROM orders 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_orders = cur.fetchall()
        cur.close()
        return render_template('admin_recent_orders.html', recent_orders=recent_orders)
    return redirect(url_for('admin_login'))

@app.route('/admin/orders')
def admin_orders():
    if 'loggedin' in session and session.get('is_admin'):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                id,
                customer_id,
                items,
                total_price,
                delivery_address,
                created_at 
            FROM orders
        """)
        orders = cur.fetchall()
        cur.close()
        # Make sure items are properly formatted, assuming items is a JSON string or similar
        for order in orders:
            order['items'] = eval(order['items'])  # Only use eval if you are sure items is a trusted source
        return render_template('admin_view_orders.html', orders=orders)
    return redirect(url_for('admin_login'))




@app.route('/admin/update_product/<int:product_id>', methods=['GET', 'POST'])
def admin_update_product(product_id):
    if 'loggedin' in session and session.get('is_admin'):
        product = fetch_product(product_id)  # Fetch the product details using the existing function
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            category = request.form['category']
            dietary_preference = request.form['dietary_preference']
            image_url = request.form['image_url']
            
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE products
                SET name = %s, description = %s, price = %s, category = %s, dietary_preference = %s, image_url = %s
                WHERE product_id = %s
            """, (name, description, price, category, dietary_preference, image_url, product_id))
            mysql.connection.commit()
            cur.close()
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))  # Redirect to admin products page after updating

        return render_template('admin_add_product.html', product=product)  # Render the form with existing product details

    return redirect(url_for('admin_login'))  # Redirect to admin login if not logged in or not admin

@app.route('/admin/users')
def admin_users():
    if 'loggedin' in session and session.get('is_admin'):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM accounts")
        users = cur.fetchall()
        cur.close()
        return render_template('admin_users.html', users=users)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(host="localhost", port=7898, debug=True)
