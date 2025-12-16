from db.service_db import create_db, insert_data, print_db

test_vvod = [
    {"username": "NIKITA", "password": "qwert123", "status": "online"},
    {"username": "ANTON", "password": "qwert", "status": "online"},
]


def main():
    create_db()
    insert_data(test_vvod, "user")
    res = print_db("user")
    for i in res:
        print(i.username, i.password, i.status)


if __name__ == "__main__":
    main()
