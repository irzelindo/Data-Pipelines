#Instructions
#In this exercise, we’ll refactor a DAG with a single overloaded task into a DAG with several tasks with well-defined boundaries
#1 - Read through the DAG and identify points in the DAG that could be split apart
#2 - Split the DAG into multiple PythonOperators
#3 - Run the DAG

import datetime
import logging

from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook

from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator


#
# TODO: Finish refactoring this function into the appropriate set of tasks,
#       instead of keeping this one large task.
#
def load_and_analyze(*args, **kwargs):
    redshift_hook = PostgresHook("redshift")

    # Find all trips where the rider was under 18
    redshift_hook.run("""
        BEGIN;
        DROP TABLE IF EXISTS younger_riders;
        CREATE TABLE younger_riders AS (
            SELECT * FROM trips WHERE birthyear > 2000
        );
        COMMIT;
    """)
    records = redshift_hook.get_records("""
        SELECT birthyear FROM younger_riders ORDER BY birthyear DESC LIMIT 1
    """)
    if len(records) > 0 and len(records[0]) > 0:
        logging.info(f"Youngest rider was born in {records[0][0]}")

        
def bike_riden():
    redshift_hook = PostgresHook("redshift")
    # Find out how often each bike is ridden
    redshift_hook.run("""
        BEGIN;
        DROP TABLE IF EXISTS lifetime_rides;
        CREATE TABLE lifetime_rides AS (
            SELECT bikeid, COUNT(bikeid) AS rides
            FROM trips
            GROUP BY bikeid
        );
        COMMIT;
    """)
    records = redshift_hook.get_records("""
        Select bikeid, rides from lifetime_rides ORDER BY rides DESC LIMIT 5                     
    """)
    logging.info(records)
    if len(records) > 0 and len(records[0]) > 0:
        logging.info(f"The bike whose ID is {records[0][0]} was riden {records[0][1]} times")

        
def number_of_stations():
    redshift_hook = PostgresHook("redshift")
    # Count the number of stations by city
    redshift_hook.run("""
        BEGIN;
        DROP TABLE IF EXISTS city_station_counts;
        CREATE TABLE city_station_counts AS(
            SELECT city, COUNT(city) AS stations
            FROM stations
            GROUP BY city
        );
        COMMIT;
    """)
    records = redshift_hook.get_records("""
        Select city, stations from city_station_counts ORDER BY stations DESC LIMIT 5                     
    """)
    logging.info(records)
    if len(records) > 0 and len(records[0]) > 0:
        logging.info(f"{records[0][0]} has {records[0][1]} stations.")

        
def log_oldest():
    redshift_hook = PostgresHook("redshift")
    records = redshift_hook.get_records("""
        SELECT birthyear FROM older_riders ORDER BY birthyear ASC LIMIT 1
    """)
    if len(records) > 0 and len(records[0]) > 0:
        logging.info(f"Oldest rider was born in {records[0][0]}")

        
dag = DAG(
    "lesson3.exercise2",
    start_date=datetime.datetime.utcnow()
)

load_and_analyze = PythonOperator(
    task_id='load_and_analyze',
    dag=dag,
    python_callable=load_and_analyze,
    provide_context=True,
)

create_oldest_task = PostgresOperator(
    task_id="create_oldest",
    dag=dag,
    sql="""
        BEGIN;
        DROP TABLE IF EXISTS older_riders;
        CREATE TABLE older_riders AS (
            SELECT * FROM trips WHERE birthyear > 0 AND birthyear <= 1945
        );
        COMMIT;
    """,
    postgres_conn_id="redshift"
)

log_oldest_task = PythonOperator(
    task_id="log_oldest",
    dag=dag,
    python_callable=log_oldest
)

bike_riden = PythonOperator(
    task_id="bike_riden",
    dag=dag,
    python_callable=bike_riden
)

number_of_stations = PythonOperator(
    task_id="number_of_stations",
    dag=dag,
    python_callable=number_of_stations
)

load_and_analyze >> create_oldest_task
create_oldest_task >> log_oldest_task
log_oldest_task >> bike_riden
bike_riden >> number_of_stations
