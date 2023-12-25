from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import os
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
from cloudinary import config, uploader
from cloudinary.uploader import upload


load_dotenv()
app = Flask(__name__, static_folder='./build', static_url_path='/')
CORS(app)

url = os.getenv('mongodb_url')
client_name = os.getenv('client_name')
users_collection_name = os.getenv('users_collection_name')


client = MongoClient(url,tlsAllowInvalidCertificates=True)
mongo = client[client_name]

config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('API_KEY'),
    api_secret=os.getenv('API_SECRET')
)




@app.route('/', defaults={'path': ''})
@app.route('/<path>')
def index(path):
    return app.send_static_file('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        
        # Assuming you are storing users in the 'users' field within the 'ProjectDetails' collection
        project = mongo.ProjectDetails.find_one({'users.email': email})
        
        if project:
            if bcrypt.checkpw(password.encode('utf-8'), project['password']):
                for user in project['users']:
                    if user['email'] == email:
                        user_data = {
                            'project_id':str(project['_id']),
                            'name': user['name'],
                            'email': user['email'],
                            'isAdmin': project['isAdmin']
                        }
                        response = make_response(jsonify({'message': 'Login Successful', 'user': user_data}))

                        return response
            else:
                response = make_response(jsonify({'message': "Invalid password"}))
                return response


        response = make_response(jsonify({'message': "Invalid email"}))
        return response

    except Exception as e:
        response = make_response(jsonify({'message': str(e)}))
        return response




@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        project_name = data.get('project_name')
        company_name = data.get('company_name')
        password = data.get('password')
        users = data.get('users')

        # Check if the project name or company name is already registered
        project = mongo.ProjectDetails.find_one({'project_name': project_name})
        if project:
            return jsonify({'message': 'Project with the same name already exists'})


        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Assuming you have a separate collection for projects, insert the project details
        project_data = {
            'users':users,
            'project_name': project_name,
            'company_name': company_name,
            'password': hashed_password,
            'isAdmin':'false',
            'registration_time': datetime.now(),
        }
        mongo.ProjectDetails.insert_one(project_data)

        return jsonify({'message': 'Successfully Registered, Please login now.'}), 200

    except Exception as e:
        return jsonify({'message': str(e)})
    



@app.route('/api/projects', methods=['GET'])
def get_users():
    projects = []
    for project in mongo.ProjectDetails.find():
        project_data = {
            'id': str(project['_id']),
            'project_name': str(project['project_name']),
            'company_name': project['company_name'],
            'registration_time': project['registration_time'],
            'users': project['users'],
            'isAdmin': project['isAdmin']

        }
        projects.append(project_data)
    response = make_response(jsonify({'projects': projects}))
    return response




@app.route('/api/projects/<id>', methods=['DELETE'])
def delete_user(id):
    result = mongo.ProjectDetails.delete_one({'_id': ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Project deleted successfully'})
    else:
        return jsonify({'message': 'Project not found'})
    





@app.route('/api/update_project', methods=['POST'])
def update_user():
    user_mail = request.json.get('user_mail')
    facebook_authenticate_token = request.json.get('facebook_authenticate_token')
    ews_instance_url= request.json.get('ews_instance_url')
    facebook_accountID = request.json.get('facebook_accountID')
    selectedCities = request.json.get('selectedCities')
    user = mongo[users_collection_name].find_one({'email': user_mail})
    update_time = datetime.now()

    if user:
        update_data = {}

        if isinstance(facebook_authenticate_token, str) and facebook_authenticate_token.strip() != '':
            update_data['facebook_authenticate_token'] = facebook_authenticate_token
            update_data['facebook_api_time'] = update_time


        if isinstance(facebook_accountID, str) and facebook_accountID.strip() != '':
            update_data['facebook_accountID'] = facebook_accountID

        if isinstance(ews_instance_url, str) and ews_instance_url.strip() != '':
            update_data['ews_instance_url'] = ews_instance_url

        if isinstance(selectedCities, list) and len(selectedCities) > 0:
            update_data['selectedCities'] = selectedCities

        if update_data:
            mongo[users_collection_name].update_one({'email': user_mail}, {'$set': update_data})
            return jsonify({'message': 'User updated successfully'})
        else:
            return jsonify({'message': 'No valid data provided to update'})

    else:
        return jsonify({'message': 'User not found.'})
    


@app.route('/api/upload-raster', methods=['POST'])
def upload_raster():
    try:
        files = request.files
        print(files)
        uploaded_files = []
        

        for file_key in files:
            file = files[file_key]
            if file:
                response = uploader.upload(file, folder="raster_files")
                uploaded_files.append({
                    'file_key': file_key,
                    'url': response['secure_url']
                })
        print(uploaded_files)

        return jsonify({'message': 'Raster files uploaded successfully', 'uploaded_files': uploaded_files})

    except Exception as e:
        return jsonify({'message': str(e)})
    




if __name__ == '__main__':
    app.run(debug=True)