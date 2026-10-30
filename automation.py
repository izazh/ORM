
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from datetime import datetime


ORANGEHRM_URL = "https://opensource-demo.orangehrmlive.com"


def create_browser():

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    return driver


def login_to_orangehrm(driver, username, password):

    wait = WebDriverWait(driver, 20)

    driver.get(ORANGEHRM_URL)

    # Enter username
    wait.until(
        EC.visibility_of_element_located(
            (By.NAME, "username")
        )
    ).send_keys(username)

    # Enter password
    driver.find_element(
        By.NAME, "password"
    ).send_keys(password)

    # Click Login
    driver.find_element(
        By.XPATH, "//button[@type='submit']"
    ).click()

    # Verify dashboard
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h6[text()='Dashboard']")
        )
    )

    print("Login successful!")


def navigate_to_pim(driver):

    wait = WebDriverWait(driver, 20)

    # Click PIM
    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='PIM']")
        )
    ).click()

    print("PIM opened successfully!")


def add_employee(
    username,
    password,
    first_name,
    middle_name,
    last_name,
    employee_id
):

    driver = None

    try:

        os.makedirs("screenshots", exist_ok=True)

        driver = create_browser()

        wait = WebDriverWait(driver, 20)

        # Open OrangeHRM and login
        login_to_orangehrm(driver, username, password)

        # Navigate to PIM
        navigate_to_pim(driver)

        # Click Add Employee
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(., 'Add Employee')]")
            )
        ).click()

        # Wait for employee form
        wait.until(
            EC.visibility_of_element_located(
                (By.NAME, "firstName")
            )
        )

        # Enter first name
        driver.find_element(
            By.NAME, "firstName"
        ).send_keys(first_name)

        # Enter middle name
        driver.find_element(
            By.NAME, "middleName"
        ).send_keys(middle_name or "")

        # Enter last name
        driver.find_element(
            By.NAME, "lastName"
        ).send_keys(last_name)


        employee_id_field = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//label[contains(normalize-space(), 'Employee Id')]/../following-sibling::div//input"
                )
            )
        )

        requested_id = str(employee_id).strip()

        # Read automatically generated ID
        initial_id = employee_id_field.get_attribute("value")

        print("Initial generated Employee ID:", repr(initial_id))

        # Select the entire existing value
        employee_id_field.click()
        employee_id_field.send_keys(Keys.CONTROL, "a")
        employee_id_field.send_keys(Keys.BACKSPACE)

        # Check that existing value is removed
        cleared_id = employee_id_field.get_attribute("value")

        print("Employee ID after clearing:", repr(cleared_id))

        if cleared_id != "":
            raise Exception(
                f"Unable to clear existing Employee ID: {cleared_id}"
            )

        # Enter requested Employee ID
        employee_id_field.send_keys(requested_id)

        # Verify actual displayed value
        entered_id = employee_id_field.get_attribute("value")

        print("Requested Employee ID:", requested_id)
        print("Final Employee ID:", entered_id)

        # Stop if ID does not match
        if entered_id != requested_id:
            raise Exception(
                f"Employee ID mismatch! "
                f"Expected: {requested_id}, "
                f"Actual: {entered_id}"
            )

        # Screenshot before saving
        driver.save_screenshot(
            "screenshots/employee_before_save.png"
        )

        # Click Save
        driver.find_element(
            By.XPATH,
            "//button[@type='submit']"
        ).click()

        # Verify Personal Details page
        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h6[text()='Personal Details']")
            )
        )

        # Screenshot after saving
        driver.save_screenshot(
            "screenshots/employee_created.png"
        )

        print("Employee creation form submitted successfully!")

        return {
            "status": "success",
            "message": "Employee created successfully!",
            "employee_id": requested_id,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name
        }

    except Exception as error:

        print("Employee Creation Error:", error)

        if driver:
            try:
                driver.save_screenshot(
                    "screenshots/employee_creation_error.png"
                )
            except Exception:
                pass

        return {
            "status": "error",
            "message": str(error)
        }

    finally:

        if driver:
            driver.quit()




def verify_and_export_employee(username, password, employee_id):
    import os
    import csv
    from datetime import datetime

    driver = None

    try:
        os.makedirs("exports", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)

        driver = create_browser()
        wait = WebDriverWait(driver, 20)

        # Step 1: Login
        login_to_orangehrm(driver, username, password)

        # Step 2: Navigate to PIM
        navigate_to_pim(driver)

        # Step 3: Open Employee List
        employee_list = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='Employee List']")
            )
        )
        employee_list.click()

        # Step 4: Locate Employee ID search field
        employee_id_field = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//label[contains(normalize-space(), 'Employee Id')]/../following-sibling::div//input"
                )
            )
        )

        employee_id_field.click()
        employee_id_field.send_keys(Keys.CONTROL, "a")
        employee_id_field.send_keys(Keys.BACKSPACE)
        employee_id_field.send_keys(str(employee_id).strip())

        # Step 5: Click Search
        search_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Search']")
            )
        )
        search_button.click()

        # Step 6: Wait for search results
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@role='table']")
            )
        )

        # Allow the table to refresh
        wait.until(
            lambda d: (
                len(d.find_elements(
                    By.XPATH,
                    "//div[@role='row'][.//div[@role='cell']]"
                )) > 0
                or len(d.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'No Records Found')]"
                )) > 0
            )
        )

        # Step 7: Extract table headers
        headers = driver.find_elements(
            By.XPATH,
            "//div[@role='row'][1]//div[@role='columnheader']"
        )

        column_names = [
            header.text.strip()
            for header in headers
        ]

        # Step 8: Extract employee records
        rows = driver.find_elements(
            By.XPATH,
            "//div[@role='row'][.//div[@role='cell']]"
        )

        employee_records = []

        for row in rows:
            cells = row.find_elements(
                By.XPATH,
                ".//div[@role='cell']"
            )

            values = [
                cell.text.strip()
                for cell in cells
            ]

            if values and column_names:
                record = dict(zip(column_names, values))
                employee_records.append(record)

        # Step 9: Verify exact Employee ID
        matching_records = [
            record for record in employee_records
            if str(
                record.get("Id", record.get("Employee Id", ""))
            ).strip() == str(employee_id).strip()
        ]

        if not matching_records:
            driver.save_screenshot(
                "screenshots/employee_verification_failed.png"
            )

            return {
                "status": "error",
                "message": (
                    f"Employee ID {employee_id} was not found "
                    "in the Employee List."
                )
            }

        # Step 10: Export extracted records to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_file = os.path.join(
            "exports",
            f"employees_{timestamp}.csv"
        )

        with open(
            csv_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=column_names
            )

            writer.writeheader()
            writer.writerows(employee_records)

        # Step 11: Screenshot
        driver.save_screenshot(
            "screenshots/employee_verification_success.png"
        )

        return {
            "status": "success",
            "message": "Employee verified and CSV exported successfully.",
            "employee_id": employee_id,
            "employee": matching_records[0],
            "total_records": len(employee_records),
            "csv_file": csv_file
        }

    except Exception as e:

        if driver:
            driver.save_screenshot(
                "screenshots/employee_verification_error.png"
            )

        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        if driver:
            driver.quit()

            
if __name__ == "__main__":

    print("OrangeHRM Automation Module")
