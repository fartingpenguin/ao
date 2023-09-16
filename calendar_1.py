from __future__ import print_function

import time
import datetime
import os.path
from dateutil.relativedelta import relativedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import googlemaps
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

# API for Google Maps
gmaps = googlemaps.Client(key=os.getenv('api_key'))

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    time_range= input("How far forward would you like to plan? ")
    home = input("Where is home? ")

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        if time_range == 'week':
            time_max = (datetime.datetime.utcnow() + relativedelta(weeks=1)).isoformat() + 'Z'
        elif time_range == 'month':
            time_max = (datetime.datetime.utcnow() + relativedelta(months=1)).isoformat() + 'Z'
        elif time_range == 'year':
            time_max = (datetime.datetime.utcnow() + relativedelta(years=1)).isoformat() + 'Z'

        print(f'Getting the upcoming events for the next {time_range}')
        events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=time_max,
                                            singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Convert the date and time format to a more readable format
            start_datetime = datetime.datetime.fromisoformat(start)
            end_datetime = datetime.datetime.fromisoformat(end)
            
            # Extract the day, date, start time, and end time
            start_day = start_datetime.strftime('%A')
            start_date = start_datetime.strftime('%d %B %Y')
            end_day = end_datetime.strftime('%A')
            end_date = end_datetime.strftime('%d %B %Y')
            start_time = start_datetime.strftime('%I:%M %p')
            end_time = end_datetime.strftime('%I:%M %p')
            previous_end_location = home
            location = event.get('location', 'No location provided')
            start_location = previous_end_location
            
            # Print the event details
            if(start_date == end_date):
                print(f"{start_day} {start_date} {start_time} -> {end_time} {event['summary']} Location: {location} ")

            else:
                print(f"{start_day} {start_date} {start_time} -> {end_day} {end_date} {end_time} {event['summary']} Location: {location}")
            
            # Get the distance between the locations
            enabled = input("Enabled? ")
            if enabled == 'yes':
                distance(start_location, location)
            # Get travel times for different modes of transportation
                modes = ['driving', 'transit', 'bicycling', 'walking']
                for mode in modes:
                    duration = time_taken(start_location, location, mode)
                    print(f"Travel time by {mode}: {duration}")
                previous_end_location = location

            if enabled == 'no':
                print("Not enabled")

    except HttpError as error:
        print('An error occurred: %s' % error)

def distance (start_location, location):
    result = gmaps.distance_matrix(start_location, location)
    # Print the result
    print("The distance from {} to {} is {}.".format(start_location, location, result["rows"][0]["elements"][0]["distance"]["text"]))

def time_taken(start_location, location, mode):
    distance_result = gmaps.distance_matrix(start_location, location, mode)

    # Get duration from result
    for row in distance_result['rows']:
        for element in row['elements']:
            duration = element['duration']['text']
            return duration

if __name__ == '__main__':
    while True:
        main()
        time.sleep(2)