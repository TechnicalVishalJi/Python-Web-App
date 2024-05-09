from flask import Flask, render_template, Response
from flask_sse import sse

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route("/stream")
def stream_text():
  stream = generate_response_stream()  # Call the modified function
  return Response(stream_generator(stream), mimetype='text/event-stream')

#functions

def stream_generator(stream):
  for chunk in stream:
    if chunk.choices[0].delta.content:
      yield f"data: {chunk.choices[0].delta.content}\n\n"
  yield "data: endfilewithcode0034\n\n"

def generate_response_stream():
    from g4f.client import Client
    from g4f.Provider import OpenaiChat
    client = Client(
       provider=OpenaiChat
    )
    #client = Client()
    stream = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[{"role": "user", "content": "Write an article on ai"}],
      stream=True
    )
    return stream
