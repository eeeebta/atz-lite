import json

from flask import Flask, render_template, request, Response, redirect
from werkzeug.exceptions import HTTPException, default_exceptions, InternalServerError

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        roster = []
        # TODO make this look nicer -- done
        # TODO now add JavaScript to prompt before submission (!!)
        if not request.files.get("roster"):
            return throw_web_error("Roster file not uploaded", 404)
        else:
            roster = [line.decode() for line in request.files.get("roster").readlines()]
            print(roster)

        merged_files_arr = []
        if request.form.get("sep_uploads") == "on":
            # Grab all 4 files here
            print(request.form.get("sep_uploads"))

            temp_file_arr = []

            if request.files.get("attendance_1"):
                temp_file_arr.append(request.files.get("attendance_1").readlines())
            if request.files.get("attendance_2"):
                temp_file_arr.append(request.files.get("attendance_2").readlines())
            if request.files.get("attendance_3"):
                temp_file_arr.append(request.files.get("attendance_3").readlines())
            if request.files.get("attendance_4"):
                temp_file_arr.append(request.files.get("attendance_4").readlines())

            merged_files_arr = [line.decode().lower() for file in temp_file_arr for line in file]

            print(merged_files_arr)
        else:
            # Do the regular stuff
            # Grab all the uploaded files and then merge them
            files = request.files.getlist("attendance_m")

            # TODO fix error message
            if len(files) < 1:
                return throw_web_error("Files not attached", 404)

            # Otherwise continue on looking at the files and then decode the contents of those files
            merged_files_arr = [contents.decode().lower() for file in files for contents in file.readlines()]

            # Generate function used to return the file, but won't be used here
            # def generate():
            #     for file_content in merged_files_arr:
            #         yield "".join(file_content)

            print("off")

        # Process roster file

        # Load dictionary
        student_dict = json.loads(roster[1])
        student_list = []

        print(student_dict)

        found_id = False

        # TODO might do a recode here cause this is sort of messy
        # Check if the roster file is valid
        processed_file_arr = []
        split_with_code = ""
        if len(roster) < 1 or roster[0] != "--------ROSTER_HEAD--------\n":
            return "roster is not valid"
        try:
            student_list = student_dict["NO_ID"]
            for student in student_list:
                for message in merged_files_arr:
                    if student in message:
                        processed_file_arr.append(student)
            print(f"MERGED_ARR: {merged_files_arr}")
            print(f"LIST: {student_list}")
            # Process without IDs cause it's not a json/python dict
        except KeyError:
            try:

                print(f"MERGED_ARR: {merged_files_arr}")
                processed_file_arr = []
                class_codes = []
                for key, val in student_dict.items():
                    if key != "NO_ID":
                        class_codes.append(key)
                        student_list = val

                for key in class_codes:
                    for message in merged_files_arr:
                        if key in message:
                            # Strip both characters because then this way it works for both windows and mac
                            processed_file_arr.append(message.split(" : ")[1].strip("\n").strip("\r"))

                found_id = True
                split_with_code = {}
                for code in class_codes:
                    split_with_code[code] = []

                for code in class_codes:
                    for student in processed_file_arr:
                        if code in student:
                            split_with_code[code].append(student.split(f" {code}")[0])

                print(f"SPLIT_: {split_with_code}")
                print(f"MERGED_1: {merged_files_arr}")
                print(f"CCODES: {class_codes}")
                print(f"PROCESSED: {processed_file_arr}")
                print(f"STUDENT_DICT: {student_dict}")
            except KeyError:
                return "Invalid structure of roster"

        if found_id:
            print("do the other stuff")
            absent = get_absent_with_code(student_dict, split_with_code)
            print(f"ABSENT1: {absent}")
            print(f"ABSENT1: {absent}")
            print(f"ABSENT1: {absent}")
            return render_template("index.html", render_absent_skeleton=True, students=student_list, absent=absent,
                                   using_dict=found_id)

        students = set(processed_file_arr)
        print(f"PROCESSED_SET: {set(processed_file_arr)}")

        absent = get_absent(student_list, students)
        print(f"ABSENT: {absent}")
        print(f"ABSENT: {absent}")

        # Return the merged file
        # return Response(generate(), mimetype="text/plain",
        #                headers={"Content-Disposition": "attachment;filename=test.txt"})

        # TODO redirect somewhere else
        return render_template("index.html", message="E", students=students, absent=absent, using_dict=found_id)
    else:
        return render_template("index.html")


@app.route("/create_roster", methods=["GET", "POST"])
def create_roster():
    if request.method == "POST":

        class_and_students = {}

        if request.form.get("do_not_use_class_ids") == "on":
            print(request.form.get("do_not_use_class_ids"))
            if request.form.get("students_1") == "":
                return "Students field cannot be empty"
            class_and_students["NO_ID"] = request.form.get("students_1").lower().split(",")

            for student in class_and_students["NO_ID"]:
                if student[0] == " ":
                    class_and_students["NO_ID"][class_and_students["NO_ID"].index(student)] = student[1:]
            print(class_and_students)
        else:
            class_id_1 = request.form.get("class_id_1").lower()
            class_id_2 = request.form.get("class_id_2").lower()
            class_id_3 = request.form.get("class_id_3").lower()
            class_id_4 = request.form.get("class_id_4").lower()

            if (class_id_1 in {class_id_2, class_id_3, class_id_4} and class_id_1 != "") or (
                    class_id_2 in {class_id_1, class_id_3, class_id_4} and class_id_2 != "") or (
                    class_id_3 in {class_id_1, class_id_2, class_id_4} and class_id_3 != "") or (
                    class_id_4 in {class_id_1, class_id_2, class_id_3} and class_id_4 != ""):
                return "Two or more Class IDs are the same"

            # TODO Look at generation of files with comma space
            students_1 = [student.lower() for student in request.form.get("students_1").split(", ")]
            students_2 = [student.lower() for student in request.form.get("students_2").split(", ")]
            students_3 = [student.lower() for student in request.form.get("students_3").split(", ")]
            students_4 = [student.lower() for student in request.form.get("students_4").split(", ")]

            # TODO handle more errors and edge cases
            if len(class_id_1) > 1 and len(students_1) > 1:
                class_and_students[class_id_1] = students_1
            else:
                return render_template("error.html", message="The first Class ID/Period field was left blank. Please "
                                                             "select the \"Do Not Use Class IDs/Periods\" box if you "
                                                             "would like to only look at students through their zoom "
                                                             "name in chat as opposed to analyzing for specific text.")

            if len(class_id_2) > 1 and len(students_2) > 1:
                class_and_students[class_id_2] = students_2
            if len(class_id_3) > 1 and len(students_3) > 1:
                class_and_students[class_id_3] = students_3
            if len(class_id_4) > 1 and len(students_4) > 1:
                class_and_students[class_id_4] = students_4

        def generate():
            return f"--------ROSTER_HEAD--------\n{json.dumps(class_and_students)}\n--------END_OF_FILE--------"

        # Return the roster
        return Response(generate(), mimetype="text/plain",
                        headers={"Content-Disposition": "attachment;filename=upload_this_roster.txt"})
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


def get_absent(roster, students):
    absent_students = roster.copy()
    for student in roster:
        for present_student in students:
            if student == present_student:
                absent_students.remove(student)
    return absent_students


def get_absent_with_code(roster, students):
    absent_students = {}
    for class_code, student_list in roster.items():
        absent_students[class_code] = []
    # TODO BUGFIX: One potential bug is that if a code in the roster is there, but then the code isn't in the student's
    #  list then that will break this program
    for class_code, student_list in roster.items():
        for roster_student in student_list:
            if roster_student not in students[class_code]:
                absent_students[class_code].append(roster_student.title())
    return absent_students


def throw_web_error(message, e_code=400):
    """Render message as an apology to user."""
    return render_template("error.html", top=e_code, bottom=message), e_code


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return throw_web_error(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
