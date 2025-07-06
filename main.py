from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

"""
to run the server :-
------------------
1. select the interpreter from .venv
2. activate the venv --> source ./.venv/bin/activate
3. uvicorn main:app --reload
"""
app = FastAPI()

load_dotenv() 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # access token (JWT) will expire in 30 minutes after it's issued.

#-------------------------------------------------------------------------------------------------------------------------------
# create test endpoint to test server.s
@app.get("/test/{item_id}/")
async def test(item_id:str):
    return{"the item id is ": item_id}

#-------------------------------------------------------------------------------------------------------------------------------
# dummy database
dummy_db = {
    "ehab":{
        "username":"ehab",
        "full name": "batman",
        "email": "e4ehap@gmail.com",
        "hashed_password": "$2b$12$4ulnQhnvgnW3kg3PdxbwuunLgngvEvRqwGj0MIST9CHHTWJzxo1yu",
        "disabled" : False # in case you signed-in but the access token is expired or invalid
    }
}
#-------------------------------------------------------------------------------------------------------------------------------
# models
class Token(BaseModel): # class token inherit from BaseModel
    access_token: str # The JWT access token
    token_type: str # bearer


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel): #This is a public-facing user model. It describes how a user should be represented in API responses (e.g. /users/me).
    username: str
    email: str | None = None #none means this fields are optional
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str
    
#-------------------------------------------------------------------------------------------------------------------------------
pwd_context = CryptContext( #This line sets up password hashing using the passlib library
    schemes=["bcrypt"], # Use the bcrypt algorithm
    deprecated="auto" # # Automatically handle deprecated schemes (older or insecure hashing schemes)
    )
# example usage --> hashed = pwd_context.hash("mysecret")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") 
# This line tells FastAPI how to extract the JWT token from requests using the OAuth2 standard.

#-------------------------------------------------------------------------------------------------------------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#-------------------------------------------------------------------------------------------------------------------------------
def get_password_hash(password):
    return pwd_context.hash(password)

#-------------------------------------------------------------------------------------------------------------------------------
def get_user(dummy_db, username: str): #take two arguments the database and username  
    if username in dummy_db:
        user_data = dummy_db[username]
        return UserInDB(**user_data)

#-------------------------------------------------------------------------------------------------------------------------------
def authenticate_user(dummy_db, username: str, password: str):
    user = get_user(dummy_db, username)  # Calls get_user function
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or invalid credentials"
        )
    
    if not verify_password(password, user.hashed_password):  # Calls verify_password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    return user

#-------------------------------------------------------------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None): #expiration time (timedelta) not required
    #Creates and returns a JWT (JSON Web Token) containing the given data, with an expiration time.
    
    to_encode = data.copy() #Make a copy of the data dictionary so you don’t modify the original.

    if expires_delta: #if expiration time (timedelta) is passed : set the expiration 
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire}) #Add the expiration time ("exp") to the payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) #encode the jwt
    return encoded_jwt #Returns the token string (e.g. eyJhbGciOi...), which can be sent to the client and used for authorization.

#-------------------------------------------------------------------------------------------------------------------------------
#the following fun is used to:
"""
1.Extract and decode the JWT token sent in the request.

2.Validate the token.

3.Find the corresponding user in the database.

4.Return the User object if everything is valid — or raise 401 Unauthorized if not.
"""
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    This uses Depends(oauth2_scheme) to:
       1. Extract the JWT from the Authorization: Bearer <token> header.
       2. Inject the token as a parameter into the function.
    """
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"WWW-Authenticate": "Bearer"}
                                         )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        """
        Decodes the JWT using your SECRET_KEY and ALGORITHM (e.g. HS256).
        Returns the payload, which is a dict (e.g., {"sub": "ehab", "exp": ...}).
        """
        username: str = payload.get("sub") #JWT should contain a "sub" field = subject = username, if missing then the token is invalid
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(dummy_db, username=token_data.username) # After successful decoding, the function looks up the user in database.
    if user is None:
        raise credential_exception

    return user
"""
why sub? ( subject-> (e.g. username or user ID))

{
  "sub": "ehab",      (subject)
  "exp": 1720193193,  (expiration time)
  "iat": 1720189593   (issued ate)
}

"""

#-------------------------------------------------------------------------------------------------------------------------------
#the following fun is used to:
"""
make sure the user is not disabled or inactive. (in case you signed-in but the access token is expired or invalid)
"""
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)): # must get an output from get_current_user() first
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user

#-------------------------------------------------------------------------------------------------------------------------------
# write a tooken root
"""
1.Accepts username and password from the client (like Postman or a frontend login form).

2.Verifies the credentials.

3.If valid, generates a JWT access token.

4.Returns it in the format defined by the Token model.
"""
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(dummy_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

#-------------------------------------------------------------------------------------------------------------------------------

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": 1, "owner": current_user}]
#-------------------------------------------------------------------------------------------------------------------------------
# << dubugging section >>
"""
pwd= get_password_hash("ehab123")
print (pwd)

print("password hash is "+get_password_hash("ehab123"))
print("SECRET_KEY = ", SECRET_KEY)
print("ALGORITHM = ", ALGORITHM)
"""

