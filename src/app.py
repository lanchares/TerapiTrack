from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "¡Hola, mundo desde TerapiTrack!"

@app.route('/about')
def about():
    return "Esta es la página sobre nosotros."

if __name__ == '__main__':
    app.run(debug=True)

# Modificación para probar la integración con Jira

