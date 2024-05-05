import json
from webdriver_setup import setup_driver
from schedule import select_schedule

def main():
    driver = setup_driver()
    try:
        driver.get("https://timetable.ksu.edu.ru/")
        schedule_json = select_schedule(driver)
        print(json.dumps(schedule_json))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
