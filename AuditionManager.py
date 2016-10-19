#!/usr/bin/python3
from audition.models import *
from datetime import *


def add_minutes(base_time, minutes):
    return (datetime.combine(date(year=1900, month=1, day=1), base_time)
            + timedelta(minutes=minutes)).time()


def manage_users():
    print()
    users = User.query.all()

    if len(users) == 0:
        print('No users in database')

    for user in users:
        print(str(user.id) + ': ' + user.username + ' - ' + user.get_full_name())

    print('Available Options:')
    print('a - Add user')
    print('d - Delete user')
    print('x - Return to main menu')

    option = input('Choose an option: ')

    if option == 'a':
        username = input('Enter username: ')
        first = input('Enter first name: ')
        last = input('Enter last name: ')
        password = input('Enter password: ')
        password2 = input('Confirm password: ')

        if password != password2:
            print('Passwords did not match!')
            manage_users()
            return

        user = User(username=username, first_name=first, last_name=last)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        manage_users()
        return

    elif option == 'd':
        id = input('Enter a user ID to delete: ')
        user = User.query.get(id)

        if user is not None:
            db.session.delete(user)
            db.session.commit()
            print('User deleted')

        else:
            print('User does not exist')

        manage_users()
        return

    elif option == 'x':
        main()
        return

    manage_users()


def manage_audition(slot):
    pass


def add_auditions(day):
    print('Bulk adding auditions to ' + day.get_date_string())
    start_time = input('Please enter a start time in the format HH:MM (24hr): ')
    start_time = datetime.strptime(start_time, '%H:%M').time()

    end_time = input('Enter the time that auditions should finish at (HH:MM): ')
    end_time = datetime.strptime(end_time, '%H:%M').time()

    duration = int(input('Enter the duration of each audition in minutes: '))
    between = int(input('Enter number of minutes between each audition (default 0): ') or 0)

    last_time = start_time

    auditions = []

    while last_time < end_time:
        audition_start = last_time
        audition_end = add_minutes(audition_start, duration)

        audition = Audition(start_time=audition_start, end_time=audition_end, audition_day=day)
        db.session.add(audition)

        auditions.append(audition)

        last_time = add_minutes(audition_end, between)

    db.session.commit()

    print('The following auditions were generated:')

    for audition in auditions:
        print(str(audition))

    print()
    print('================================================================================')

    manage_day(day)


def manage_day(day):
    print()
    print('Viewing ' + day.get_date_string() + ' for show ' + day.show.name)

    if len(day.auditions) == 0:
        print('There are no auditions on this day')

    for i in range(0, len(day.auditions)):
        print(str(i + 1) + ' - ' + str(day.auditions[i].start_time) + ' - ' + str(day.auditions[i].end_time))

    print('Available Options:')
    print('a - Bulk add new auditions')
    print('x - Return to previous menu')
    option = input('Please select a day or an option')

    if option == 'a':
        add_auditions(day)
        return

    elif option == 'x':
        manage_days(day.show)
        return

    else:
        audition_index = int(option) - 1
        manage_audition(day.auditions[audition_index])


def add_day(show):
    print()
    print('Adding a new date to ' + show.name)
    date_string = input('Please enter a date in the form DD/MM/YY')

    given_date = datetime.strptime(date_string, '%d/%m/%y').date()

    print('The given date is ' + given_date.strftime('%A %d %B %Y'))
    answer = input('Is this correct? [Y/n]').lower()

    if answer == '' or answer == 'y' or answer == 'yes':
        day = AuditionDay(show=show, date=given_date)
        db.session.add(day)
        db.session.commit()
        print('Day added.')
        manage_days(show)

    else:
        print('Aborted.')
        manage_days(show)


def manage_days(show):
    print()

    if len(show.audition_days) > 0:
        print('Existing audition days:')
        for i in range(0, len(show.audition_days)):
            print(str(i + 1) + ' - ' + show.audition_days[i].get_date_string())

    print('Available options:')
    print('a - Add new day')
    print('x - Return to show menu')
    option = input('Please select a day or an option')

    if option == 'a':
        add_day(show)
        return

    elif option == 'x':
        manage_show(show)
        return

    else:
        day_index = int(option) - 1
        manage_day(show.audition_days[day_index])


def create_show():
    print()
    name = input('Enter name for new show: ')
    show = Show(name=name)

    print('Adding show ' + show.name)
    db.session.add(show)
    db.session.commit()

    main()


def manage_show(show):
    print()
    print('Managing show ' + show.name)
    print('Available options:')
    print('m - Manage audition days')
    print('d - Delete Show')
    print('x - Return to main menu')

    option = input('Please select an option: ').lower()

    if option == 'm':
        manage_days(show)
        return

    elif option == 'd':
        print('You are about to delete the show. This cannot be undone!')
        print('To confirm, please type the name of the show (case sensitive)')

        show_name = input()

        if show_name == show.name:
            db.session.delete(show)
            db.session.commit()

            print('Show deleted. Returning to menu')

        else:
            print('Name did not match. Returning to menu')

        main()
        return

    elif option == 'x':
        main()


def main():
    print()
    shows = Show.query.all()

    if len(shows) == 0:
        print('There are no shows in the database. Creating one now...')
        create_show()
        return

    else:
        print('Available shows in Database:')

        for i in range(0, len(shows)):
            print(str(i + 1) + ' - ' + shows[i].name)

        print('Available options:')
        print('a - Add new show')
        print('u - Manage Users')
        print('x - Exit')

        option = input('Please select a show or enter an option')

        if option == 'x':
            return

        elif option == 'a':
            create_show()
            return

        elif option == 'u':
            manage_users()
            return

        option = int(option)

        if option > len(shows):
            print('Number specified outside of range. Exiting')
            return

        manage_show(shows[option - 1])


print('audition Management Tool')
main()
