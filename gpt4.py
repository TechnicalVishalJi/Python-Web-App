from g4f.client import Client
from g4f.Provider import RetryProvider, Phind, FreeChatgpt, Liaobots

client = Client(
provider=RetryProvider([Phind, FreeChatgpt, Liaobots], shuffle=False)
)

stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "How to create a flask app"}],
    stream=True

)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content or "", end="")
