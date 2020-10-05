from flask import Flask, render_template, request, Response

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":

        # Grab all the uploaded files and then merge them
        files = request.files.getlist("attendance")
        merged_files_arr = []
        for file in files:
            for contents in file.readlines():

                # Decode the message cause apparently bytes aren't meant to be read by humans, lol
                merged_files_arr.append(contents.decode())

        def generate():
            for file_content in merged_files_arr:
                yield "".join(file_content)

        # Return the merged file
        return Response(generate(), mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=test.txt"})
    else:
        return render_template("index.html")


@app.route("/create_roster", methods=["GET", "POST"])
def create_roster():
    if request.method == "POST":
        return "generate the roster file here"
    else:
        return render_template("create_roster.html")


@app.route("/stitch", methods=["GET", "POST"])
def stitch():
    if request.method == "POST":
        return "stitched file"
    else:
        return render_template("stitch.html")


@app.route("/test")
def gen_file_for_dl():
    gen = ""

    def generate():
        for row in ["E", "E", "E", "E", "E", "E", "E", "E", "E", "E", "E", "E"]:
            yield ", ".join(row) + "\n"

    return Response(generate(), mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=test.txt"})


def process_files(roster, attendance_file):
    # Structure should follow: {"Class": ["Students", "for", "class", "go" "here"], "Class2": []}
    absent_students = {}
    return absent_students
