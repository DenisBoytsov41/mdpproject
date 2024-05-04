from webdriver_setup import setup_driver
from schedule import select_schedule


def main():
    driver = setup_driver()
    try:
        driver.get("https://timetable.ksu.edu.ru/")
        select_schedule(driver)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
