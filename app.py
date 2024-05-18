from flask import Flask, render_template, Response, url_for, render_template_string, request, send_from_directory
import json
import mysql.connector
import os
from flask_cors import CORS
import uuid
from g4f.cookies import set_cookies
import requests

app = Flask(__name__)

query = ""
totalResponse = ""
CORS(app, resources={r"/deleteaihistory": {"origins": "https://app.vishal.rf.gd"}})
UPLOAD_FOLDER = os.path.join('uploads', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
set_cookies(".google.com", {
    "__Secure-1PSID": os.environ['GEMINI_COOKIE1'],
    "__Secure-1PSIDCC": os.environ['GEMINI_COOKIE2'],
    "__Secure-1PSIDTS" : os.environ['GEMINI_COOKIE3']
})
set_cookies(".bing.com", {
    "_U": os.environ['BING_COOKIE']
})

@app.route('/')
def index():
    return ai()
    #return render_template('index.html')

@app.route('/ai')
def ai():
    user_logged_in = request.cookies.get('userLoggedIn')

    if user_logged_in == 'YES':
        logo = url_for('static', filename='img/logo.png')
        copyBtn = url_for('static', filename='img/copy-btn.png')
        loadingDots = url_for('static', filename='img/loadingdots.gif')
        image_paths = [logo, copyBtn, loadingDots]
        return render_template('ai.html', image_paths=image_paths)
    else:
        # User is not logged in
        return render_template_string('You are not logged in and hence not allowed to access this page')  

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/saveaihistory')
def savehistory():
    user_history = get_user_history()
    if(user_history):
        result = saveUserHistToDb(user_history)
        if(result):
            if(result == "No new history"):
                return render_template_string("<h1>History in database already contains history of server</h1>")
            elif(result is True):
                return render_template_string("<h1>Saved history to database successfully</h1>")
            else:
                return render_template_string("<h1>Error while saving history to database</h1>")
        else:
            return render_template_string("<h1>Can't save history to database</h1>")
    else:
        answer = "History from database was'nt saved to server!"
        if(writeDbHistoryToServer()):
            answer = "History from database was saved to server!"
        return render_template_string(f"<h1>No history found on server<br><br>{answer}</h1>")

@app.route("/deleteaihistory", methods=["POST"])
def deleteaihistory():
    if request.method == 'POST':
        if request.form.get('q') != 'delete':
            return "Invalid request"
    else:
        return "Invalid request"

    with open("user_history.txt", "w"):
        pass
    connection = connectMysql()
    cursor = connection.cursor()

    # Query to select history where user_id is 123
    user_id = 123
    query = 'DELETE FROM ai_user_history WHERE user_id = %s'
    cursor.execute(query, (user_id,))
    deleteSuccess = False
    if cursor.rowcount > 0:
        deleteSuccess = True

    connection.commit()

    # Closing cursor and connection
    cursor.close()
    connection.close()
    if(deleteSuccess):
        return Response("History deleted successfully",mimetype='text/plain')
    else:
        return Response("History deleted from server but not found on database",mimetype='text/plain')

@app.route("/ai/retrieveaihistory", methods=["POST"])
def retrieveaihistory():
    if request.method == 'POST':
        if request.form.get('q') != 'retrieve':
            return "Invalid request"
    else:
        return "Invalid request"

    history = get_user_history()
    return json.dumps(history)


@app.route('/uploadimage', methods=['POST'])
def upload_image():
    if 'image' in request.files:
        image = request.files['image']
        # Save the image to a directory or process it as needed
        image_name = uuid.uuid4().hex + "-" + image.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
        image.save(image_path)
        
        with open("uploads/uploads.txt", "w") as file:
            file.write("img/"+image_name)
        return "../uploads/img/" + image_name
    else:
        return 'No image file received'

@app.route('/searchimages', methods=['POST'])
def searchimages():
    if request.method == "POST":
        if request.get_json().get('q') != 'search':
            return "Invalid request"
    else:
        return "Invalid request"
        
    resultDict = searchImages(request.get_json().get('query'))
    if "items" in resultDict:
        return json.dumps({"items":resultDict["items"]})
    elif "error" in resultDict:
        return json.dumps({"error":resultDict["error"]})
    else:
        return json.dumps({"error": "Something went wrong while getting images!"})

@app.route('/uploads/img/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/cron')
def cron():
    return render_template_string("<h1>Cron Done</h1>")
    

@app.route("/ai/gpt35/<string:prompt>")
def gpt35(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  stream = gpt35_generate_response_stream(prompt)  # Call the modified function
  return Response(stream_generator(stream, "GPT 3.5"), mimetype='text/event-stream')

@app.route("/ai/gpt4/<string:prompt>")
def gpt4(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  stream = gpt4_generate_response_stream(prompt)  # Call the modified function
  return Response(stream_generator(stream, "GPT 4"), mimetype='text/event-stream')

@app.route("/ai/gpt4o/<string:prompt>")
def gpt4o(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  stream = gpt4o_generate_response_stream(prompt)  # Call the modified function
  return Response(stream_generator(stream, "GPT 4o"), mimetype='text/event-stream')

@app.route("/ai/gpt4vision/<string:prompt>")
def gpt4vision(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  responseList = gpt4vision_generate_response_stream(prompt)  # Call the modified function
  if(responseList is not None):
      stream = responseList[0]
      imagePath = responseList[1]
      return Response(stream_generator(stream, "GPT 4",imagePath), mimetype='text/event-stream')
  else:
      return Response("Error while generating response endfilewithcode0034", mimetype='text/event-stream')
      
@app.route("/ai/geminipro/<string:prompt>")
def geminipro(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  stream = geminipro_generate_response_stream(prompt)  # Call the modified function
  return Response(stream_generator(stream, "Gemini Pro"), mimetype='text/event-stream')

@app.route("/ai/geminiflash/<string:prompt>")
def geminiflash(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  return Response(gemini15flash_generate_response_stream(prompt), mimetype='text/event-stream')

@app.route("/ai/geminiprovision/<string:prompt>")
def geminiprovision(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  responseList = geminiprovision_generate_response_stream(prompt)  # Call the modified function
  stream = responseList[0]
  imagePath = responseList[1]
  return Response(stream_generator(stream, "Gemini Pro",imagePath), mimetype='text/event-stream')

@app.route("/ai/copilot/<string:prompt>")
def copilot(prompt):
  global query
  global totalResponse
  query = prompt
  totalResponse = ""
  stream = copilot_generate_response_stream(prompt)  # Call the modified function
  return Response(stream_generator(stream, "Copilot"), mimetype='text/event-stream')

@app.route("/ai/dalle3/<string:prompt>")
def dalle3(prompt):
    global query
    global totalResponse
    query = prompt
    totalResponse = ""
    imageUrls = dalle3_generate_response(prompt)  # Call the modified function
    if(imageUrls):
        templateString = ""
        for imageUrl in imageUrls:
            templateString += f"<img src='{imageUrl}' width='100%' class='generated-image' alt='Generated Image'><br><br>"
        addNewHistoryToServer(prompt, "Dall-E 3", templateString)
        return render_template_string(templateString)
    else:
        return render_template_string("Error while generating image")

@app.route("/ai/geminiimage/<string:prompt>")
def geminiimage(prompt):
    global query
    global totalResponse
    prompt = "Generate an image described as:\n" + prompt
    query = prompt
    totalResponse = ""
    imageUrls = gemini_image_generate_response(prompt)  # Call the modified function
    if(imageUrls):
        templateString = ""
        for imageUrl in imageUrls:
            templateString += f"<img src='{imageUrl}' width='100%' class='generated-image' alt='Generated Image'><br><br>"
        addNewHistoryToServer(prompt, "Gemini Image", templateString)
        return render_template_string(templateString)
    else:
        return render_template_string("Error while generating image")

#functions

def connectMysql():
    return mysql.connector.connect(
        host=os.environ["HOST"],
        user=os.environ["USER"],
        password=os.environ["DBPASS"],
        database=os.environ["DBNAME"]
    )

def saveUserHistToDb(fileHistory):
    # Establishing the connection
    connection = connectMysql()
    # Creating a cursor object
    cursor = connection.cursor()

    # Query to select history where user_id is 123
    user_id = 123
    table_name = "ai_user_history"
    query = f"SELECT user_history FROM {table_name} WHERE user_id = %s"

    # Executing the query
    cursor.execute(query, (user_id,))

    # Fetching the result
    row = cursor.fetchone()
    newHist = []
    if row:
        savedDbHist = json.loads(row[0])  # Assuming history is the first column in the result
        
        try:
            first_equal_index = savedDbHist.index(fileHistory[0])
        except ValueError:
            first_equal_index = None

        if first_equal_index is not None:
            # Check if subsequent elements of list1 match subsequent elements of list2
            matching_indices = [i for i in range(len(savedDbHist) - first_equal_index) if fileHistory[i] == savedDbHist[first_equal_index + i]]

            if len(matching_indices) > 0:
                # Remove matched elements from list2
                fileHistory = fileHistory[len(matching_indices):]

        
        # Create a new list with elements of list2 after removal
        if(fileHistory):
            newHist = savedDbHist + fileHistory
            with open('user_history.txt', 'w'):
                pass  # Pass is used to do nothing in the body of the with statement

            with open('user_history.txt', 'a') as file:              
                for dict in newHist:
                    file.write(json.dumps(dict) + '\n')
        else:
            with open('user_history.txt', 'w'):
                pass  # Pass is used to do nothing in the body of the with statement
            
            with open('user_history.txt', 'a') as file:              
                for dict in savedDbHist:
                    file.write(json.dumps(dict) + '\n')

            # Closing cursor and connection
            cursor.close()
            connection.close()
            
            return "No new history"
        
    else:
        newHist = fileHistory
        
    
    newHistList = json.dumps(newHist)
    print("histList:        "+ newHistList + "\n\n\n")
    query = 'INSERT INTO ai_user_history (user_id, user_history) VALUES (%s, %s) ON DUPLICATE KEY UPDATE user_history = VALUES(user_history);'
    newdata = (user_id, newHistList)
    cursor.execute(query, newdata)
    saveSuccessful = False
    # Checking if the insertion was successful
    if cursor.rowcount > 0:
        saveSuccessful = True

    # Committing the changes to the database
    connection.commit()

    # Closing cursor and connection
    cursor.close()
    connection.close()
    return saveSuccessful

def writeDbHistoryToServer():
    # Establishing the connection
    connection = connectMysql()
    # Creating a cursor object
    cursor = connection.cursor()

    # Query to select history where user_id is 123
    user_id = 123
    table_name = "ai_user_history"
    query = f"SELECT user_history FROM {table_name} WHERE user_id = %s"

    # Executing the query
    cursor.execute(query, (user_id,))

    # Fetching the result
    row = cursor.fetchone()
    if row:
        with open('user_history.txt', 'a') as file:              
            for dict in json.loads(row[0]):
                file.write(json.dumps(dict) + '\n')
        return True
    return False
    
def stream_generator(stream, aiName, imagePath=None):
  for chunk in stream:
    response = chunk.choices[0].delta.content
    if response:
      responseReplaced = response.replace('\n', '~n~')
      yield f"data: {responseReplaced}\n\n"
      global totalResponse
      totalResponse += response
  yield "data: endfilewithcode0034\n\n"
  addNewHistoryToServer(query, aiName, totalResponse, imagePath)
    
def gpt35_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import OpenaiChat
    client = Client(
       provider=OpenaiChat
    )
    stream = client.chat.completions.create(
      model ="gpt-3.5-turbo",
      messages = prepareHistoryForAi(prompt), 
      #response_format = { "type": "json_object" },
      stream=True
    )
    return stream

def gpt4o_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import OpenaiChat
    client = Client(
       provider=OpenaiChat
    )

    stream = client.chat.completions.create(
      model ="gpt-4o",
      messages = prepareHistoryForAi(prompt),     
      #response_format = { "type": "json_object" },
      stream=True
    )
    return stream

def gpt4_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import OpenaiChat
    client = Client(
       provider=OpenaiChat
    )
    
    stream = client.chat.completions.create(
      model ="gpt-4",
      messages = prepareHistoryForAi(prompt),     
      #response_format = { "type": "json_object" },
      stream=True
    )
    return stream
    
def gpt4vision_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import OpenaiChat
    
    client = Client(
       provider=OpenaiChat
    )
    imagePath = None
    with open("uploads/uploads.txt", "r") as file:
        imagePath = file.read()
    if(imagePath==""):
        return None

    stream = client.chat.completions.create(
          model="gpt-4",
          messages = [{"role":"user", "content":prompt}],
          image=open("uploads/"+imagePath, "rb"),         
          stream=True
        )
    with open("uploads/uploads.txt", "w"):
        pass
    return [stream,imagePath]

def geminipro_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import GeminiPro
    
    client = Client(
       api_key=os.environ["GEMINIAPI1"],
       provider=GeminiPro
    )
    
    stream = client.chat.completions.create(
      model = "gemini-1.5-pro-latest",
      messages = prepareHistoryForAi(prompt),
      temperature = 0.5,
      top_p = 1,
      top_k = 10,
      stream=True
    )
    return stream

def gemini15flash_generate_response_stream(prompt):
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINIAPI1"])

    generation_config = {
      "temperature": 1,
      "top_p": 0.95,
      "top_k": 64,
      "max_output_tokens": 8192,
      "response_mime_type": "text/plain",
    }
    safety_settings = [
      {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
      },
      {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
      },
      {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
      },
      {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
      },
    ]

    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash-latest",
      safety_settings=safety_settings,
      generation_config=generation_config,
    )

    messages = prepareHistoryForAi(prompt, True)
    
    stream = model.generate_content(messages, stream=True)

    for chunk in stream:
        response = chunk.text
        if response:
          responseReplaced = response.replace('\n', '~n~')
          yield f"data: {responseReplaced}\n\n"
          global totalResponse
          totalResponse += response
    yield "data: endfilewithcode0034\n\n"
    addNewHistoryToServer(query, "Gemini Flash", totalResponse)


def geminiprovision_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import GeminiPro
    client = Client(
       api_key=os.environ["GEMINIAPI"],
       provider=GeminiPro
    )
    imagePath = None
    with open("uploads/uploads.txt", "r") as file:
        imagePath = file.read()
    stream = client.chat.completions.create(
          model ="gemini-1.5-pro-latest",
          messages = prepareHistoryForAi(prompt),#[{"role":"user", "content":prompt}],
          image=open("uploads/"+imagePath, "rb"),
          temperature = 1,
          max_tokens = 8000,
          top_p = 0.8,
          top_k = 10,
          stream=True
        )
    with open("uploads/uploads.txt", "w"):
        pass
    return [stream,imagePath]

def copilot_generate_response_stream(prompt):
    from g4f.client import Client
    from g4f.Provider import Bing
    
    client = Client(
       provider=Bing
    )

    stream = client.chat.completions.create(
      model ="Balanced",
      messages = prepareHistoryForAi(prompt),
      stream=True
    )
    return stream
    
def dalle3_generate_response(prompt):
    from g4f.client import Client
    from g4f.Provider import BingCreateImages
    
    client = Client(
        image_provider=BingCreateImages
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt
    )
    imageUrls = []
    for imageObj in response.data:
        imageUrls.append(imageObj.url)
    return imageUrls

def gemini_image_generate_response(prompt):
    from g4f.client import Client
    from g4f.Provider import Gemini

    client = Client(image_provider=Gemini)

    response = client.images.generate(
        model="gemini",
        prompt=prompt
    )
    imageUrls = []
    for imageObj in response.data:
        imageUrls.append(imageObj.url)
    return imageUrls

def append_to_user_history(data):
  with open('user_history.txt', 'a') as file:
      file.write(json.dumps(data) + '\n')

def get_user_history():
  try:
      with open('user_history.txt', 'r') as file:
          history_list = [json.loads(line) for line in file]
      return history_list
  except FileNotFoundError:
      return []

def get_user_historyWithoutImageAi():
  try:
      with open('user_history.txt', 'r') as file:
          history_list = [json.loads(line) for line in file]
          modifiedHistList = []
          for object in history_list:
            if "aiName" in object:
                if object["aiName"] != "Dall-E 3" and object["aiName"] != "Gemini Image":
                    modifiedHistList.append(object)
                else:
                    modifiedHistList.pop()
            else:
                modifiedHistList.append(object)                
      return modifiedHistList
  except FileNotFoundError:
      return []

def removeAiName(history):
  newHist = []
  for dict in history:
    dict.pop("aiName", None)
    newHist.append(dict)
  return newHist

def prepareHistoryForAi(prompt, google=False):
    history = removeAiName(get_user_historyWithoutImageAi())
    if google:
        modifiedHistory = []
        for object in history:
            if(object["role"]== "assistant"):
                modifiedHistory.append({"role": "model", "parts": [object["content"]]})
            else:
                modifiedHistory.append({"role": object["role"], "parts": [object["content"]]})
        modifiedHistory.append({"role": "user", "parts": [prompt]})
        #modifiedHistory.insert(0, {"role": "system", "parts": ["You are a helpful assistant."]})
        return modifiedHistory
    
    history.append({"role": "user", "content": prompt})
    history.insert(0, {"role": "system", "content": "You are a helpful assistant."})
    return history

def addNewHistoryToServer(prompt, ainame, response, imagePath=None):
    if(imagePath is None):
        append_to_user_history({"role": "user", "content": prompt})
    else:
        append_to_user_history({"role": "user", "content": prompt+"<br><br><img style='width:40%; border-radius:10px;' src='../uploads/"+imagePath+"'>"})
    append_to_user_history({"role": "assistant", "aiName":ainame, "content": response})

def searchImages(query):
    searchEndpoint = "https://www.googleapis.com/customsearch/v1"
    accessKey = os.environ["GOOGLE_ACCESSKEY"]
    cx = os.environ["GOOGLE_CX"]
            
    params = {
        "q": query,
        "searchType": "image",
        "cx" : cx,
        "key": accessKey
    }

    try:
        # Making the GET request
        response = requests.get(searchEndpoint, params=params)

        # If the request was successful
        if response.status_code == 200:
            # Assuming the response is in JSON format and is a dictionary
            data = response.json()
            return data
        else:
            return {"errorCode":str(response.status_code), "error": "Can't get images, quota exceeded"}
    except Exception as e:
        return {'error': "Internal Server Error while getting images", "errorCode": "500"}




########## File Manager code starts ############


from flask import jsonify
import shutil

BASE_DIR = os.path.abspath(".")

@app.route('/vsftp')
def vsftp():
    return render_template('vsftp.html')

@app.route('/vsftp/list', methods=['GET'])
def list_files():
    path = request.args.get('path', BASE_DIR)
    if not os.path.exists(path):
        return jsonify({"error": "Path does not exist"}), 400

    files = []
    folders = []
    for entry in os.scandir(path):
        if entry.is_file():
            files.append(entry.name)
        else:
            folders.append(entry.name)

    return jsonify({"path": path, "files": files, "folders": folders})

@app.route('/vsftp/create', methods=['POST'])
def create():
    data = request.get_json()
    path = data.get('path')
    type = data.get('type')
    name = data.get('name')

    if type == 'file':
        open(os.path.join(path, name), 'w').close()
    elif type == 'folder':
        os.makedirs(os.path.join(path, name), exist_ok=True)

    return jsonify({"status": "success"})

@app.route('/vsftp/delete', methods=['POST'])
def delete():
    data = request.get_json()
    path = data.get('path')

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

    return jsonify({"status": "success"})

@app.route('/vsftp/move', methods=['POST'])
def move():
    data = request.get_json()
    src = data.get('src')
    dst = data.get('dst')

    shutil.move(src, dst)

    return jsonify({"status": "success"})

@app.route('/vsftp/copy', methods=['POST'])
def copy():
    data = request.get_json()
    src = data.get('src')
    dst = data.get('dst')

    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    else:
        shutil.copy2(src, os.path.join(dst, os.path.basename(src)))

    return jsonify({"status": "success"})

@app.route('/vsftp/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'GET':
        path = request.args.get('path')

        with open(path, 'r') as file:
            content = file.read()
        return jsonify({"content": content})

    elif request.method == 'POST':
        data = request.get_json()
        path = data.get('path')
        content = data.get('content')

        with open(path, 'w') as file:
            file.write(content)

        return jsonify({"status": "success"})
    else:
        return "invalid request"



########### File Manager code ends here ###########



if __name__ == '__main__':
    app.run(debug=True)
