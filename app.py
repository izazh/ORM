
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from automation import add_employee, verify_and_export_employee

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

os.makedirs(EXPORT_FOLDER, exist_ok=True)


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/start-automation", methods=["POST"])
def start_automation():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    first_name = data.get("first_name", "").strip()
    middle_name = data.get("middle_name", "").strip()
    last_name = data.get("last_name", "").strip()
    employee_id = data.get("employee_id", "").strip()

    # Validate required fields
    if not all([
        username,
        password,
        first_name,
        last_name,
        employee_id
    ]):
        return jsonify({
            "status": "error",
            "message": "Please fill in all required fields."
        }), 400

    try:

        # STEP 1: Create employee
        print("STEP 1: Starting employee creation...")

        creation_result = add_employee(
            username,
            password,
            first_name,
            middle_name,
            last_name,
            employee_id
        )

        if creation_result.get("status") != "success":
            return jsonify({
                "status": "error",
                "stage": "creation",
                "message": "Employee creation failed.",
                "details": creation_result
            }), 500

        print("Employee created successfully!")

        # STEP 2: Verify employee and export CSV
        print("STEP 2: Starting employee verification...")

        verification_result = verify_and_export_employee(
            username,
            password,
            employee_id
        )

        if verification_result.get("status") != "success":
            return jsonify({
                "status": "error",
                "stage": "verification",
                "message": "Employee created, but verification failed.",
                "creation": creation_result,
                "verification": verification_result
            }), 500

        print("Employee verified and CSV exported!")

        # STEP 3: Get CSV filename
        csv_path = verification_result.get("csv_file", "")
        csv_filename = os.path.basename(csv_path)

        full_csv_path = os.path.join(
            EXPORT_FOLDER,
            csv_filename
        )

        if not csv_filename or not os.path.isfile(full_csv_path):
            return jsonify({
                "status": "error",
                "stage": "csv_export",
                "message": "CSV file was not found."
            }), 500

        # STEP 4: Return final result
        return jsonify({
            "status": "success",
            "message": "Employee created, verified and exported successfully!",
            "employee_id": employee_id,
            "employee": verification_result.get("employee"),
            "total_records": verification_result.get("total_records"),
            "csv_file": csv_filename,
            "download_url": f"/download-csv/{csv_filename}"
        }), 200

    except Exception as e:

        print("Automation error:", str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# STEP 5: Download CSV
@app.route("/download-csv/<path:filename>")
def download_csv(filename):

    # Validate filename
    if filename != os.path.basename(filename):
        return jsonify({
            "status": "error",
            "message": "Invalid filename."
        }), 400

    file_path = os.path.join(EXPORT_FOLDER, filename)

    if not os.path.isfile(file_path):
        return jsonify({
            "status": "error",
            "message": "CSV file not found."
        }), 404

    return send_from_directory(
        EXPORT_FOLDER,
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
