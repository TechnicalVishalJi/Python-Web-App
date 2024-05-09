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
  def generate():
    from g4f.client import Client
    #from g4f.Provider import RetryProvider, Phind, FreeChatgpt, Liaobots
    client = Client(
    #provider=RetryProvider([Phind, FreeChatgpt, Liaobots, OpenAi], shuffle=False)
    )

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Write an article on ai"}],
        stream=True
    )

    #print("\n\nAi Answer\n")
    #for chunk in stream:
     #   if chunk.choices[0].delta.content:
    #        print(chunk.choices[0].delta.content or "", end="")
           
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield f"data: {chunk.choices[0].delta.content}\n\n"
        elif not chunk.choices[0].delta.content:  # Assuming empty content indicates end
            break
    
  return Response(generate(), mimetype="text/event-stream")
