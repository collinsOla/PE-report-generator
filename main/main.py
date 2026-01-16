from main.fetch_articles import main
from main.analysis import writeReport

end = False
while not(end):
    print("Enter 1 to generate data for the database, press 2 to write a report ")
    inp = input()
    if (inp == '1'):
        main()
    elif (inp =='2'):
        f = input("Please enter file path (.pdf):  ")
        writeReport(f)

    print("Succesfully done, Enter 1 to continue, 2 to quit")
    inp = input()
    if inp == '2':
        end = True