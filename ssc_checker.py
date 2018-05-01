from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

def getGrades(username, password):
    options = Options()
#    options.add_argument("--headless")

    browser = webdriver.Firefox(firefox_options=options)
    browser.delete_all_cookies()
    browser.implicitly_wait(1)

    grades = []

    print(f'Looking up grades for {username}')

    try:
        browser.get('https://ssc.adm.ubc.ca/sscportal/servlets/SRVAcademicRecord?context=html')

        try:
            print('Logging in')
            username_input = browser.find_element_by_id("username")
            password_input = browser.find_element_by_id("password")
            username_input.send_keys(username)
            password_input.send_keys(password, Keys.ENTER)
        except NoSuchElementException:
            pass

        try:
            print('Looking for nav buttons')
            navbar = browser.find_element_by_xpath('//*[@id="tabs"]/ul')
        except NoSuchElementException:
            print("Nav buttons not found, is SSC down?")
            browser.quit()
            return None

        yearButton = navbar.find_element_by_xpath('//a[@href="#tabs-all"]')

        # reaaaally make sure we clicked it
        yearButton.click()
        yearButton.click()
        yearButton.click()
        yearButton.click()
        yearButton.click()

        try:
            print("Looking for main table")
            table = browser.find_element_by_tag_name('tbody')
        except NoSuchElementException:
            print("Main table not found, is SSC down?")
            browser.quit()
            return None

        courses = []
        index = 0
        while True:
            try:
                course = table.find_element_by_xpath(f'//*[@id="row-all-{str(index)}"]')
            except NoSuchElementException:
                break

            courses.append(course)
            index += 1

        for course in courses:
            data = course.find_elements_by_tag_name('td')

            course_name =   data[0].text
            section =       data[1].text
            grade =         data[2].text
            letter =        data[3].text
            session =       data[4].text
            term =          data[5].text
            program =       data[6].text
            year =          data[7].text
            credits =       data[8].text
            average =       data[9].text
            standing =      data[10].text

            data = {
                    'course_name': course_name,
                    'section':     section,
                    'grade':       grade,
                    'letter':      letter,
                    'session':     session,
                    'term':        term,
                    'program':     program,
                    'year':        year,
                    'credits':     credits,
                    'average':     average,
                    'standing':    standing,
                    }

            grades.append(data)

        browser.quit()
        return grades


    except WebDriverException:
        print("Error: WebDriverException!")
        browser.quit()
        return None
