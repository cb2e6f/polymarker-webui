import sys

from flask import Flask

# Create the Flask application
app = Flask(__name__)


# Define a route for the home page
@app.route('/')
def hello_world():
    return 'Hello, World!!!E!!!!'


# Define another route for a different page
@app.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}!'


# Add a main function to run the Flask app via the command line
def main2():
    app.run(debug=True)


def main():
    print(sys.argv)
    if len(sys.argv) > 1:
        if sys.argv[1] == "add":
            print("add genome")
            exit(0)

    print("run app?")
    app.run(debug=True)


if __name__ == "__main__":
    main()
