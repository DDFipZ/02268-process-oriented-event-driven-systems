import json
import sys
from time import time, sleep
from datetime import datetime
import random
import requests
from pytimedinput import timedInput

# siddhi event processor
target_url = "http://0.0.0.0:7370/train"

CURRENT_TRAIN = 5467  # get real train ID

TRAIN_CAPACITY = 300


# generates a value for the speed parameter, based on probabilities
def speed_generator():
    i = random.randint(1, 100)
    if i < 20:
        return random.randint(10, 39)  # simulate low speed
    elif i > 90:
        return random.randint(151, 200)  # simulate high speed
    return random.randint(40, 150)  # standard speed


# generates a value for the pressure parameter, based on probabilities
def pressure_generator():
    i = random.randint(1, 100)
    if i < 5:
        return random.randint(55, 64)  # simulate low pressure
    elif i > 95:
        return random.randint(76, 90)  # simulate high pressure
    return random.randint(65, 75)  # standard pressure


# generates a value for the temperature parameter, based on probabilities
def temperature_generator():
    i = random.randint(1, 100)
    if i < 5:
        return random.randint(700, 750)  # simulate high temperature
    elif i > 95:
        return random.randint(751, 800)  # simulate very high temperature
    return random.randint(600, 699)  # standard temperature


# implements a random number of new passengers until the capacity is reached
def passengers_generator(curr_passengers):
    if curr_passengers < TRAIN_CAPACITY:
        return curr_passengers + random.randint(5, min(10, TRAIN_CAPACITY - curr_passengers))


# sets a cooldown interval between 1 and 6 minutes
def interval_generator():
    return random.randint(60, 360)


# initializes the event
def profiler():
    return {
        'event_time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'train_id': f'{CURRENT_TRAIN}',
        'speed': random.randint(40, 150),
        'pressure': random.randint(65, 75),
        'brake_temp': random.randint(600, 699),
        'passengers': random.randint(150, 250)
    }


# updates the event with a different speed value
def change_speed(event):
    event['speed'] = speed_generator()
    return event


# updates the event with a different temperature value
def change_temperature(event):
    event['brake_temp'] = temperature_generator()
    return event


# updates the event with a different pressure value
def change_pressure(event):
    event['pressure'] = pressure_generator()
    return event


# updates the event with a different passengers value
def change_passengers(event):
    event['passengers'] = passengers_generator()
    return event


def main():
    # start trip
    s = input("Enter any input to start trip.\n")
    if s is None or s == "stop":
        sys.exit("Canceled start")

    # initialize train event
    train_event = profiler()

    # send event
    r = requests.post(url=target_url, data=json.dumps(train_event), headers={"Content-Type": "application/json; "
                                                                                             "charset=utf-8"})

    # check response
    if r.status_code != 200:
        print("Post request failed.\n")
    print("Event sent successfully!\n")

    # initialize timers
    speed_init = time()
    pressure_init = time()
    temperature_init = time()
    passenger_init = time()

    speed_timeout = interval_generator()
    pressure_timeout = interval_generator()
    passenger_timeout = interval_generator()
    temperature_timeout = interval_generator()

    # continuously change values based on probabilities and time intervals, and consequent post request
    while True:
        # save current time and check all timers
        curr_time = time()

        if curr_time > speed_init + speed_timeout:
            train_event = speed_generator(train_event)
            speed_init = curr_time
            speed_timeout = interval_generator()

        if curr_time > pressure_init + pressure_timeout:
            train_event = pressure_generator(train_event)
            pressure_init = curr_time
            pressure_timeout = interval_generator()

        if curr_time > temperature_init + temperature_timeout:
            train_event = temperature_generator(train_event)
            temperature_init = curr_time
            temperature_timeout = interval_generator()

        if curr_time > passenger_init + passenger_timeout:
            train_event = passengers_generator(train_event)
            passenger_init = curr_time
            passenger_timeout = interval_generator()

        # update time stamp
        train_event['event_time'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        # post updated event
        r = requests.post(url=target_url, data=json.dumps(train_event), headers={"Content-Type": "application/json; "
                                                                                                 "charset=utf-8"})
        # check response
        if r.status_code != 200:
            print("Post request failed.\n")
        print("Event sent successfully!\n")

        # allow for input and wait 5 seconds
        user_text, timed_out = timedInput("", timeout=10)
        if not timed_out and user_text == "stop":
            break

    # set speed to 0 to represent trip end
    train_event["speed"] = 0

    # post updated event
    r = requests.post(url=target_url, data=json.dumps(train_event), headers={"Content-Type": "application/json; "
                                                                                             "charset=utf-8"})
    # check response
    if r.status_code != 200:
        print("Post request failed.\n")
    print("Event sent successfully!\n")


if __name__ == '__main__':
    main()
