from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimlarityDB
users = db["Users"]

def UserExist(username): 
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

def verifyPW(username, password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({
        "Username" : username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw)==hashed_pw:
        return True
    else:
        return False

def count_Tokens(username):
    tokens = users.find({
        "Username" : username
    })[0]["Tokens"]
    return tokens

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status" : "301",
                "msg" : "Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users.insert({
            "Username" : username,
            "Password" : hashed_pw,
            "Tokens" : 6

        })

        retJson = {
                "status" : 200,
                "msg" : "you have successfully signed up to an API "
            }
        return jsonify(retJson)
    
class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if UserExist(username):
            retJson = {
                "status" : "301",
                "msg" : "Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = verifyPW(username, password)

        if not correct_pw:
            retJson = {
            "status" : 302,
            "msg" : "Invalid Password"
            }
            return jsonify(retJson)

        num_token = count_Tokens(username)

        if num_token <= 0:
            retJson = {
            "status" : 303,
            "msg" : "Out of tokens"
            }
            return jsonify(retJson)


        # nlp = spacy.load('en_core_web_sm')
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)

        retJson = {
            "status" : 200,
            "similarity" : ratio,
            "msg" : "similarity tested successfully"
            }


        current_tokens = count_Tokens(username)

        users.update({
            "Username" : username,
        },
        {
            "$set":{
            "Tokens" : current_tokens - 1
            }
        
        })

        return jsonify(retJson)

class Refill(Resource):
    def Post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = "abc123"

        if not password == correct_pw:
            retJson = {
                "status" : 304,
                "msg" : "Invalid admin Password"
            }
            return jsonify(retJson)
        
        current_tokens = count_Tokens(username)
        users.update({
            "Username" : username
        },
        {
            "$set":{
                "Tokens": refill_amount+current_tokens
            }
        })

        retJson = {
                "status" : 200,
                "msg" : "Successfully creited"
            }
        return jsonify(retJson)

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == "__main__":
    app.run(host='0.0.0.0')

        




