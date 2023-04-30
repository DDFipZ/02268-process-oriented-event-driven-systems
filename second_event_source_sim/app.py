import json
import sys
from time import time
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
        return curr_passengers + random.randint(1, min(10, TRAIN_CAPACITY - curr_passengers))
    return curr_passengers


# sets a cooldown interval between 1 and 6 minutes
def interval_generator():
    return random.randint(60, 360)


# initializes the event
def profiler():
    return {
        'train_id': f'{CURRENT_TRAIN}',
        'speed': random.randint(40, 150),
        'pressure': random.randint(65, 75),
        'brake_temp': random.randint(600, 699),
        'passengers': random.randint(150, 250)
    }


# event with all attributes set to one to indicate trip start
def start_event():
    return {
        'train_id': f'{CURRENT_TRAIN}',
        'speed': 1,
        'pressure': 1,
        'brake_temp': 1,
        'passengers': 1
    }


# event with all attributes set to zero to indicate trip end
def end_event():
    return {
        'train_id': f'{CURRENT_TRAIN}',
        'speed': 0,
        'pressure': 0,
        'brake_temp': 0,
        'passengers': 0
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
    event['passengers'] = passengers_generator(event['passengers'])
    return event


# post request with event data do siddhi event processor
def publish_event(event):
    # post updated event
    r = requests.post(url=target_url, data=json.dumps(event), headers={"Content-Type": "application/json; "
                                                                                       "charset=utf-8"})
    # check response
    if r.status_code == 200:
        return True
    return False


def main():
    # start trip
    s = input("Enter any input to start trip.\n")
    if s is None or s == "stop":
        sys.exit("Canceled start")

    train_event = start_event()
    status = publish_event(train_event)
    if status == 0:
        print("Exiting program due to post request error.\n")
        return 1

    # initialize train event stream
    train_event = profiler()
    status = publish_event(train_event)
    if status == 0:
        print("Exiting program due to post request error.\n")
        return 1

    # initialize timers
    speed_init = time()
    pressure_init = time()
    temperature_init = time()
    passenger_init = time()

    speed_timeout = interval_generator()
    pressure_timeout = interval_generator()
    passenger_timeout = interval_generator()
    temperature_timeout = interval_generator()

    # initialize speedup factor
    speedup_factor = 1

    # continuously change values based on probabilities and time intervals, and consequent post request
    while status is True:
        # save current time and check all timers
        curr_time = time()
        print(
            f"timeouts monitor:\nspeed: {int(speed_init + (speed_timeout / speedup_factor) - curr_time)}\n"
            f"pressure: {int(pressure_init + (pressure_timeout / speedup_factor) - curr_time)}\n"
            f"temperature: {int(temperature_init + (temperature_timeout / speedup_factor) - curr_time)}\n"
            f"passenger: {int(passenger_init + (passenger_timeout / speedup_factor) - curr_time)}\n"
            f"\nspeedup factor: {speedup_factor}\n")

        if curr_time > speed_init + (speed_timeout / speedup_factor):
            train_event = change_speed(train_event)
            speed_init = curr_time
            speed_timeout = interval_generator()

        if curr_time > pressure_init + (pressure_timeout / speedup_factor):
            train_event = change_pressure(train_event)
            pressure_init = curr_time
            pressure_timeout = interval_generator()

        if curr_time > temperature_init + (temperature_timeout / speedup_factor):
            train_event = change_temperature(train_event)
            temperature_init = curr_time
            temperature_timeout = interval_generator()

        if curr_time > passenger_init + (passenger_timeout / speedup_factor):
            train_event = change_passengers(train_event)
            passenger_init = curr_time
            passenger_timeout = interval_generator()

        print(train_event)

        status = publish_event(train_event)
        if status == 0:
            print("Exiting program due to post request error.\n")
            return 1

        # allow for input and wait 10 seconds
        user_text, timed_out = timedInput("", timeout=(max(1, 5/speedup_factor)))

        # make timeouts go faster
        if not timed_out and (user_text == "fast" or user_text == "+") and speedup_factor < 100:
            speedup_factor = speedup_factor * 10

        # reset timeout speed to default
        if not timed_out and (user_text == "slow" or user_text == "-") and speedup_factor > 1:
            speedup_factor = speedup_factor / 10

        # trigger end event
        if not timed_out and user_text == "stop":
            break

    # trip end event
    train_event = end_event()

    status = publish_event(train_event)
    if status == 0:
        print("Exiting program due to post request error.\n")
        return 1

    # program ran correctly
    return 0


if __name__ == '__main__':
    main()
