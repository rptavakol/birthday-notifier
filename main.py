from datetime import date
import mysql.connector
import smtplib
import logging

# Local module that contains MySQL and email credentials
import secrets


def send_email(bdayKids, SUBJECT):
    """Sends email notification"""

    # Create email message
    msg = ""
    for index in range(len(bdayKids)):
        msg += '-> ' + str(bdayKids[index][0]) + ' ' + str(bdayKids[index][1]) + '\n'
    logging.info("\n" + msg)
    message = 'Subject: {}\n\n{}'.format(SUBJECT, msg)

    # Smtp_server configuration
    smpt_server = "smtp.gmail.com"
    port = 587

    # Connect to SMTP server and send email
    server = smtplib.SMTP(smpt_server, port)
    server.starttls()
    server.login(secrets.email["emailFrom"], secrets.email["password"])
    server.sendmail(secrets.email["emailFrom"], secrets.email["emailTo"], message)
    server.quit()

    logging.info("Email notification sent.")

    return


def run_mysql_query(query):
    """Retrieves data from mysql database using SQL query in string format"""

    logging.debug(f"Running query '{query}'..")

    try:
        cnx = mysql.connector.connect(user=secrets.db["user"], password=secrets.db["password"],
                                      host=secrets.db["host"], database=secrets.db["name"])

        # returns each sql row as dict
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(query)

        # Store queried data dicts into a list
        dbData = [row for row in cursor]

    except Exception as e:
        print("Hey, there's a DB Error: " + str(e))

    finally:
        cursor.close()
        cnx.close()


    return dbData


def get_bdaysMonth(month):
    """Runs query against db to find all the birthday kids of current month and emails user"""

    mbdayKids = list()

    # run query to return all bdays this month
    queryMonthlyBdays = "SELECT * FROM life.friends WHERE birthDay LIKE '%-{:02d}-%' and notify = 1 ORDER BY birthDay ASC".format(month)
    dbData2 = run_mysql_query(queryMonthlyBdays)

    for row in dbData2:
        mbdayKids.append([row['firstName'].strip(), row['lastName'].strip(), row['birthDay']])

    return mbdayKids


def get_bdaysToday(todayStr):
    """Runs query against db to find any friends having their birthday today"""

    bdaysToday = list()

    queryTodayBdays = f"SELECT * FROM life.friends WHERE birthDay = '{todayStr}' AND notify = 1"
    dbData1 = run_mysql_query(queryTodayBdays)

    [logging.debug(row) for row in dbData1]

    for row in dbData1:
        bdaysToday.append([row['firstName'].strip(), row['lastName'].strip(), row['birthDay']])

    return bdaysToday


#---------------------------------- MAIN ----------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO, format=' [%(levelname)s] %(message)s')
logging.info('Start of script\n')


today = date.today()
# Database date in '9999-mm-dd' format
todayStr = today.strftime("9999-%m-%d")
logging.info(today.strftime("Today is %B %d, %Y"))

try:
    # If today is first of month, send summary email of this months bday kids
    if today.day == 1:
        bdaysMonth = get_bdaysMonth(today.month)
        subject = "%s Birthdays (%d)" %(today.strftime("%B"), len(bdaysMonth))
        send_email(bdaysMonth, subject)

    # Get today's birthdays
    bdaysToday = get_bdaysToday(todayStr)
    # If there are any friends with birthdays today, send email
    if bdaysToday:
        logging.info("Birthday today!")
        # %-d removes 0 before single digit dates
        subject = "Today's Birthday Kid(s) (%s)" %today.strftime("%b %-d")
        send_email(bdaysToday, subject)

    else:
        logging.info("No birthdays today")

except Exception as e:
    # If script crashes or raises error, notify immediately
    error = f"FATAL ERROR (CHECK BDAY SCRIPT): {str(e)}"
    logging.error(error)
    send_email([], error)