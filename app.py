import json

from flask import Flask, render_template, request, Response
from werkzeug.exceptions import HTTPException, default_exceptions, InternalServerError

app = Flask(__name__)


# TODO possibly add a "view roster" page to see the students in each class?
@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        # TODO make this look nicer -- done
        # TODO now add JavaScript to prompt before submission (!!)

        # Check within the user's request that they did indeed submit a roster file
        if not request.files.get("roster"):

            # If they did not then render the error page (yes throw web error is misleading -- something to fix)
            return throw_web_error("Roster file not uploaded", 404)
        else:
            # Otherwise look at the roster and then decode it after reading in the bytes
            roster = [line.decode() for line in request.files.get("roster").readlines()]
            print(roster)

            # Check that the roster is valid
            if len(roster) < 1 or roster[0] != "--------ROSTER_HEAD--------\n":
                return throw_web_error("Roster is not valid", 404)

        # If separate uploads are on (getting the checkbox data from the HTML) then take each file
        if request.form.get("sep_uploads") == "on":
            # Grab all 4 files here
            print(request.form.get("sep_uploads"))

            # Initialize the temporary file array
            temp_file_arr = []

            # TODO clean up with a loop probably
            if request.files.get("attendance_1"):
                temp_file_arr.append(request.files.get("attendance_1").readlines())
            if request.files.get("attendance_2"):
                temp_file_arr.append(request.files.get("attendance_2").readlines())
            if request.files.get("attendance_3"):
                temp_file_arr.append(request.files.get("attendance_3").readlines())
            if request.files.get("attendance_4"):
                temp_file_arr.append(request.files.get("attendance_4").readlines())

            # Decode and make the lines lower after reading in each file and appending to temp_file_arr
            merged_files_arr = [line.decode().lower() for file in temp_file_arr for line in file]

            # TODO REMOVE DEBUGGING
            print(merged_files_arr)
        else:
            # Otherwise if separate file uploads are not enabled "do the regular stuff" as the comment here
            # previously said

            # Grab all the uploaded files from the HTML element
            files = request.files.getlist("attendance_m")

            # TODO fix error message -- done
            # Throw an error if files are not attached (at least one)
            if len(files) < 1:
                return throw_web_error("Files not attached or found", 404)

            # Otherwise decode and format the contents of each file and merge it
            merged_files_arr = [contents.decode().lower() for file in files for contents in file.readlines()]

        # Process roster file here
        # Load the actual roster from the file
        student_dict = json.loads(roster[1])
        student_list = []

        # Initialize the found_id as False because by default we assume there is no id being used
        found_id = False

        # TODO might do a recode here cause this is sort of messy with try catches everywhere
        processed_file_arr = []
        split_with_code = ""

        # TODO a much better way to do this is to loop through the keys and check if they have NO_ID or valid ids
        try:
            # Process without IDs cause it's not a json/python dict

            # First look for the the key of NO_ID and grab the stuednt list from there
            student_list = student_dict["NO_ID"]

            # Look at each student in the list
            for student in student_list:

                # Look at each message in the messages
                for message in merged_files_arr:

                    # If the student's full name is in the message, then add it to the present array
                    # TODO refactor processed_file_arr to present_students
                    if student in message:
                        processed_file_arr.append(student)
            print(f"MERGED_ARR: {merged_files_arr}")
            print(f"LIST: {student_list}")

        except KeyError:

            # If the key does not exist then try to look for valid ids
            # TODO this doesn't need to be in a try/catch -- remove?
            try:

                print(f"MERGED_ARR: {merged_files_arr}")

                # Initialize variables
                processed_file_arr = []
                class_codes = []

                # For each key/val pair in the roster of students append the key of the class to the class_codes array
                for key, val in student_dict.items():
                    if key != "NO_ID":
                        class_codes.append(key)
                        # TODO remove student list b/c it does not do anything and maybe I could repurpose it?
                        student_list = val

                for key in class_codes:
                    for message in merged_files_arr:
                        if key in message:
                            # Strip both characters because then this way it works for both windows and mac
                            processed_file_arr.append(message.split(" : ")[1].strip("\n").strip("\r"))

                # Set the found ID to True because everything looks like it worked
                found_id = True
                split_with_code = {}

                # Set classcode arrays in split_with_code
                # TODO rename to something like students in array or whatever
                for class_code in class_codes:
                    split_with_code[class_code] = []

                # Check if the class code is in the student's message and then add the student
                for class_code in class_codes:
                    for student in processed_file_arr:
                        if class_code in student:
                            split_with_code[class_code].append(student.split(f" {class_code}")[0])

                print(f"SPLIT_: {split_with_code}")
                print(f"MERGED_1: {merged_files_arr}")
                print(f"CCODES: {class_codes}")
                print(f"PROCESSED: {processed_file_arr}")
                print(f"STUDENT_DICT: {student_dict}")

            except KeyError:
                # If there are no keys or something else happens -- I don't know this could probably be removed
                return "Invalid structure of roster"

        # If class_ids are found, then return this (which is the absent students)
        # TODO possibly recode this and make this cleaner (as maybe one return statement?
        if found_id:
            absent = get_absent_with_code(student_dict, split_with_code)
            # TODO remove student list
            return render_template("index.html", render_absent_skeleton=True, students=student_list, absent=absent,
                                   using_dict=found_id)

        # Turn this into a set because the way that no_id students are handled are that only one student can exist
        # within this list, so turning this into a set makes sure that only one of each student can exist
        students = set(processed_file_arr)

        print(f"PROCESSED_SET: {set(processed_file_arr)}")

        # Get the absent students (look at function)
        absent = get_absent(student_list, students)

        # TODO fix the return/update the return statement
        return render_template("index.html", render_absent_skeleton=True, students=students, absent=absent, using_dict=found_id)
    else:
        # Just render the template without the absent skeleton
        return render_template("index.html", render_absent_skeleton=False)


# Create this new app route of "/create_roster"
@app.route("/create_roster", methods=["GET", "POST"])
def create_roster():

    # If a form is submitted then go through with this
    if request.method == "POST":

        class_and_students = {}

        # Check if the user does not want to use class_ids
        if request.form.get("do_not_use_class_ids") == "on":

            # Make sure that the first student field is not blank
            if request.form.get("students_1") == "":
                return "Students field cannot be empty"

            # Since we are not using IDs, we can just add all the students into an array under the NO_ID key
            # (after making them all lower case and splitting them by comma space)
            # TODO possible bug: user does not use comma and a space and only commas
            # TODO UPDATE: can be fixed by splitting by a comma and then stripping spaces from the end of each string
            # FIXED
            class_and_students["NO_ID"] = request.form.get("students_1").lower().split(",")

            # Check that each student's name does not have a space in front of it since we split by comma
            for student in class_and_students["NO_ID"]:
                if student[0] == " ":
                    class_and_students["NO_ID"][class_and_students["NO_ID"].index(student)] = student[1:]
            print(class_and_students)
        else:
            # TODO Probably can loop or do this better -- possibly clean this up
            class_id_1 = request.form.get("class_id_1").lower()
            class_id_2 = request.form.get("class_id_2").lower()
            class_id_3 = request.form.get("class_id_3").lower()
            class_id_4 = request.form.get("class_id_4").lower()

            # Check if class ids are the same of any class
            # TODO fix this/make it look cleaner or allow multiple class codes to exist
            if (class_id_1 in {class_id_2, class_id_3, class_id_4} and class_id_1 != "") or (
                    class_id_2 in {class_id_1, class_id_3, class_id_4} and class_id_2 != "") or (
                    class_id_3 in {class_id_1, class_id_2, class_id_4} and class_id_3 != "") or (
                    class_id_4 in {class_id_1, class_id_2, class_id_3} and class_id_4 != ""):
                return "Two or more Class IDs are the same"

            # TODO Look at generation of files with comma space -- split by comma and then clean up using a loop to
            #  strip and clean the string?
            students_1 = [student.lower() for student in request.form.get("students_1").split(", ")]
            students_2 = [student.lower() for student in request.form.get("students_2").split(", ")]
            students_3 = [student.lower() for student in request.form.get("students_3").split(", ")]
            students_4 = [student.lower() for student in request.form.get("students_4").split(", ")]

            # TODO handle more errors and edge cases
            # Make sure that at least one class id exists and that at least one student exists and add the class code
            # and the student array to that dictionary
            if len(class_id_1) > 1 and len(students_1) > 1:
                class_and_students[class_id_1] = students_1
            else:
                return throw_web_error("The first Class ID/Period field was left blank. Please select the \"Do Not "
                                       "Use Class IDs/Periods\" box if you would like to only look at students "
                                       "through their zoom name in chat as opposed to analyzing for specific text.")

            # Do the same for the other classes and students if they exist
            # TODO find a better way to handle all of this
            if len(class_id_2) > 1 and len(students_2) > 1:
                class_and_students[class_id_2] = students_2
            if len(class_id_3) > 1 and len(students_3) > 1:
                class_and_students[class_id_3] = students_3
            if len(class_id_4) > 1 and len(students_4) > 1:
                class_and_students[class_id_4] = students_4

        # Generate function that could be omitted, but generates the entire line to create the file
        # TODO: more urgent would be to detect if the system requesting is windows or mac and return a properly spaced
        #  roster for the proper operating system
        # TODO remove function?
        def generate():
            return f"--------ROSTER_HEAD--------\n{json.dumps(class_and_students)}\n--------END_OF_FILE--------"

        # Return the roster as a response object that is built to return a plain text file
        # (the headers tell the browser that it is receiving a downloadable file to be saved locally
        return Response(generate(), mimetype="text/plain",
                        headers={"Content-Disposition": "attachment;filename=upload_this_roster.txt"})
    else:
        return render_template("create_roster.html")


# Grab the absent students from the list of students and the roster
def get_absent(roster, students):
    # Create a copy of the roster
    absent_students = roster.copy()

    # For each student in the roster and for each present student within the student list: if the student in the roster
    # is equal to the present student then remove it from the absent students, which is a roster copy
    for student in roster:
        for present_student in students:
            if student == present_student:
                absent_students.remove(student)

    # Finally return this array
    return absent_students


# This function does the same thing as the other get_absent function, except that it does it for dictionaries
def get_absent_with_code(roster, students):

    # Create an EMPTY absent_students dictionary
    absent_students = {}

    # For each class and class_code within the roster items (key, val pairs) create an array in the absent students
    # dictionary with that class_code as the key
    for class_code, student_list in roster.items():
        absent_students[class_code] = []

    # TODO BUGFIX: One potential bug is that if a code in the roster is there, but then the code isn't in the student's
    #  list then that will break this program -- possibly fix by making sure that every field is filled out

    # For each class code and student list within the roster and for each student within that student listen:
    # check if that roster student is not in that class and then append it to that class_code's array
    for class_code, student_list in roster.items():
        for roster_student in student_list:
            if roster_student not in students[class_code]:
                absent_students[class_code].append(roster_student.title())

    # Finally return the dictionary
    return absent_students


def errorhandler(e):
    # Handle errors

    # Check if the error is an HTTPException, and if it isn't, then there was an internal server error
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return throw_web_error(e.name, e.code)


def throw_web_error(message, e_code=400):
    # Return the error + the sick webpage I made for it
    return render_template("error.html", top=e_code, bottom=message), e_code


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
