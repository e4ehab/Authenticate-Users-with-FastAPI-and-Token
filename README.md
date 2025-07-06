*functionalities* 
------------------
1. user_name and password for every single user
2. as soon as you sign-in you're going to be issued with a token
3. this token is jwt token (authorization token) , contains encoded data represents you , and it will have expiry data like 30 min
4. every time the user want to hit the endpoint that require authentication we're gonna submit this token
5. when a token is expired we can resent new token

-------------------------------------------------------------------------------------------------------------------------------
*dependencies*
---------------
fastapi // uvicorn[standard] // python-multipart // python-jose[cryptography] //passlib[bcrypt]

-------------------------------------------------------------------------------------------------------------------------------
*to run the server*
-------------------
1. select the interpreter from .venv
2. activate the venv --> source ./.venv/bin/activate
3. uvicorn main:app --reload

-------------------------------------------------------------------------------------------------------------------------------
*for secretkeys and alogrithms*
-------------------------------
generate 32-bit key -> openssl rand -hex 32 , then take the key generated and put it in .env file and load it in main

-------------------------------------------------------------------------------------------------------------------------------
*test using postman*
---------------------
🔐 STEP 1: Get Access Token -> [POST] http://localhost:8000/token
📬 Postman Settings:
Method: POST
Headers: (no need to manually add — form-data handles this)
Body Tab → x-www-form-urlencoded

<Key>	    <Value>
username	ehab
password	ehab123

*output*
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlaGFiIiwiZXhwIjoxNzUxODMwMzQzfQ.PTw1dRbTKl868vr6Lmni_mWz6Vae6-CE9DcNVaYKuVs",

    "token_type": "bearer"
}


🔑 STEP 2: Use the Token to Access Protected Routes -> [GET] http://localhost:8000/users/me/
📬 Postman Settings:
Method: GET
Headers Tab → Add this:

<Key>       	<Value>
Authorization	Bearer paste_your_token_here

*output*
{
    "username": "ehab",
    "email": "e4ehap@gmail.com",
    "full_name": null,
    "disabled": false
}


🔑 STEP 3 {bonus step}: Use the Token to Access Protected Routes -> [GET] http://localhost:8000/users/me/items
📬 Postman Settings:
Method: GET
Headers Tab → Add this:

<Key>       	<Value>
Authorization	Bearer paste_your_token_here

*output*
[
    {
        "item_id": 1,
        "owner": {
            "username": "ehab",
            "email": "e4ehap@gmail.com",
            "full_name": null,
            "disabled": false,
            "hashed_password": "$2b$12$4ulnQhnvgnW3kg3PdxbwuunLgngvEvRqwGj0MIST9CHHTWJzxo1yu"
        }
    }
]

------------------------------------------------------------------------------------------------------------------------------