import sqlite3
from query_serializer import QuerySerializer


def run_database_statements(statements):
    conn = sqlite3.connect('test.db')
    for statement in statements:
        conn.execute(statement)
    conn.commit()


def teardown_database():
    reset_statements = """
        DROP TABLE customer;
        DROP TABLE organization;
        DROP TABLE address;
        DROP TABLE purchase;
    """.split(";")
    run_database_statements(reset_statements)


def setup_database():
    create_statements = """
        CREATE TABLE customer (name TEXT, organization_id INT);
        CREATE TABLE organization (name TEXT, address_id INT);
        CREATE TABLE address (name TEXT);
        CREATE TABLE purchase (customer_id INT);

        INSERT INTO address (name) VALUES ("Main Address");
        INSERT INTO organization (name, address_id) VALUES ("ZeroCater", (SELECT rowid from address limit 1));
        INSERT INTO customer (name, organization_id) VALUES ("Jason", (SELECT rowid from organization limit 1));
        INSERT INTO purchase (customer_id) VALUES ((SELECT rowid from customer limit 1));
        INSERT INTO purchase (customer_id) VALUES ((SELECT rowid from customer limit 1));
    """.split(";")
    run_database_statements(create_statements)


def get_test_query():
    return """
        SELECT
            customer.rowid AS "id",
            customer.name AS "name",
            organization.rowid AS "organization__id",
            organization.name AS "organization__name",
            address.name AS "organization__address__name",
            purchase.rowid AS "purchases--__id"
        FROM
            customer
            JOIN organization ON customer.organization_id = organization.rowid
            JOIN address ON organization.address_id = address.rowid
            JOIN purchase ON customer.rowid = purchase.customer_id
    """


class SqliteCustomerPurchaseSerializer(QuerySerializer):
    def get_array_indicator(self):
        return '--'

    def execute_query(self, query, params):
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def cursor_iterator(self, cursor):
        for row in cursor.fetchall():
            yield row

    def get_columns(self, cursor):
        return [col[0] for col in cursor.description]

    def get_query_and_params(self):
        return get_test_query(), []
