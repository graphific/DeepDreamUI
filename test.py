import flask
from shelljob import proc
import eventlet
eventlet.monkey_patch()

app = flask.Flask(__name__)

@app.route( '/stream' )
def stream():
    g = proc.Group()
    p = g.run( [ "bash", "-c", "for ((i=0;i<100;i=i+1)); do echo $i; sleep 1; done" ] )
  
    #p = g.run( [ "python", "dreamer.py", "-i", "static/input", "-o", "static/output" ] )

    def read_process():
        while g.is_pending():   
            lines = g.readlines()
            for proc, line in lines:
                yield "data:" + line + "\n\n"
                #p.kill()

    return flask.Response( read_process(), mimetype= 'text/event-stream' )

@app.route('/s')
def get_page():
    return flask.send_file('console.html')

if __name__ == "__main__":
    app.run(debug=True)