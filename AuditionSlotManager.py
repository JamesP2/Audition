from AuditionSlot import *
from datetime import *


def manage_slot(slot):
    pass


def add_slots(day):
    print('Bulk adding slots to ' + day.get_date_string())
    start_time = input('Please enter a start time in the format HH:MM (24hr): ')
    start_time = datetime.strptime(start_time, '%H:%M').time()

    end_time = input('Enter the time that auditions should finish at (HH:MM): ')
    end_time = datetime.strptime(end_time, '%H:%M').time()

    duration = int(input('Enter the duration of each slot in minutes: '))
    between = int(input('Enter number of minutes between each slot (default 0): ') or 0)

    slots = []


def manage_day(day):
    print()
    print('Viewing ' + day.get_date_string() + ' for show ' + day.show.name)

    if len(day.audition_slots) == 0:
        print('There are no audition slots on this day')

    for i in range(0, len(day.audition_slots)):
        print(str(i + 1) + ' - ' + str(day.audition_slots[i].start_time) + ' - ' + str(day.audition_slots[i].end_time))

    print('Available Options:')
    print('a - Bulk add new slots')
    print('x - Return to previous menu')
    option = input('Please select a day or an option')

    if option == 'a':
        add_slots(day)
        return

    elif option == 'x':
        manage_days(day.show)
        return

    else:
        slot_index = int(option) - 1
        manage_slot(day.audition_slots[slot_index])


def add_day(show):
    print()
    print('Adding a new date to ' + show.name)
    date_string = input('Please enter a date in the form DD/MM/YY')

    given_date = datetime.strptime(date_string, '%d/%m/%y').date()

    print('The given date is ' + given_date.strftime("%A %d %B %Y"))
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
            print(str(i+1) + ' - ' + shows[i].name)

        show_index = input('Please select a show to manage, 0 to make a new one, x to exit')

        if show_index == 'x':
            return

        show_index = int(show_index)

        if show_index == 0:
            create_show()
            return

        if show_index > len(shows):
            print('Number specified outside of range. Exiting')
            return

        manage_show(shows[show_index - 1])

print('AuditionSlot Management Tool')
main()
