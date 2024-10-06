
from quart import Quart, request, redirect, url_for, Response, render_template
from quart_auth import AuthManager, AuthUser, login_required, login_user, logout_user, current_user
from dotenv import load_dotenv
import asyncpg
import os
import bcrypt
load_dotenv()
async def create_db_pool():
  return await asyncpg.create_pool(host=os.environ.get("DATABASE_HOST"),
                                   port=os.environ.get("DATABASE_PORT"),
                                   database=os.environ.get("DATABASE_NAME"),
                                   user=os.environ.get("DATABASE_USER"),
                                   password=os.environ.get("DATABASE_PASSWORD"))

async def register_user(pool, username, password):
    async with pool.acquire() as conn:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        await conn.execute(
            "INSERT INTO users (username, password_hash) VALUES ($1, $2)",
            username, password_hash
        )
        
            

async def check_password(pool, username, password):
    async with pool.acquire() as conn:
        result = await conn.fetchrow("SELECT password_hash FROM users WHERE username = $1", username)

        if result is None:
            print("User not found!")
            return False

        password_hash = result["password_hash"]

        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            print("Password is correct!")
            return True
        else:
            print("Incorrect password!")
            return False

app = Quart(__name__)
app.secret_key = 'TgyvTTtTTF76_jhvtug'
auth_manager = AuthManager(app)

@app.before_serving
async def create_db_connection():
  app.db = await create_db_pool()

@app.after_serving
async def close_db_connection():
  print("Closing connection...")
  await app.db.close()

@app.route('/')
async def index():
    return await render_template("index.html")

@app.get('/pocketsaver')
@login_required
async def pocketsaver():
    return f'Private page for {current_user.auth_id}'

@app.route('/register', methods=["POST"])
async def register():
    data = await request.form
    username = data.get("username")
    password = data.get("password")
    try:
        await register_user(app.db, username, password)
        login_user(AuthUser(username))
    except asyncpg.UniqueViolationError:
        return Response(status=409)
    return Response(status=201)

@app.route('/login', methods=["POST"])
async def login():
    data = await request.form
    username = data.get("username")
    password = data.get("password")

    if await check_password(app.db, username, password):
        login_user(AuthUser(username))
        return Response(status=200)
    return Response(status=401)


@app.route('/logout')
async def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="localhost", port=5000)
