from __future__ import print_function
from flask import Flask, render_template, request
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

app = Flask(__name__)

@app.route('/event1')
def event1():
    # Add code to handle the first event page here
    return "This is Event 1"

@app.route('/event2')
def event2():
    # Add code to handle the second event page here
    return "This is ()"

# Add more routes for other events as needed

def configure():
    load_dotenv()

# API for Google Maps
gmaps = googlemaps.Client(key=os.getenv('api_key'))

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_google_calendar_events(time_max):
    creds = None
    if os.path.exists('stuff/token.json'):
        creds = Credentials.from_authorized_user_file('stuff/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'stuff/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('stuff/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        time_range = request.form.get('time_range', 'month') 
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
        return events

    except HttpError as error:
        print('An error occurred: %s' % error)
        return []

<<<<<<< Updated upstream
=======
# Function to extract event data
def extract_event_data(event):
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

    if start_date != end_date:
        event_data = {
            'eventId': event['id'],  # Include eventId in event data
            'name': event['summary'],
            'datetime': f"{start_day} {start_date} {start_time} -> {end_day} {end_date} {end_time}",
            'location': event.get('location', 'No location provided'),
        }
    elif start_date == end_date:
        event_data = {
            'eventId': event['id'],  # Include eventId in event data
            'name': event['summary'],
            'datetime': f"{start_day} {start_date} {start_time} -> {end_time}",
            'location': event.get('location', 'No location provided'),
        }
    return event_data


# Function to configure and fetch event data
def fetch_event_data(time_range, event_name=None, event_datetime=None, event_id=None):
    google_events = get_google_calendar_events(time_range)
    
    if event_name is not None and event_datetime is not None:
        # Filter events by event_name and event_datetime
        filtered_events = [
            event for event in google_events 
            if 'summary' in event and event['summary'] == event_name and 'dateTime' in event['start'] and event['start']['dateTime'] == event_datetime
        ]
        return filtered_events

    if event_id is not None:
        # Filter events by event_id
        filtered_events = [
            event for event in google_events 
            if 'id' in event and event['id'] == event_id
        ]
        return filtered_events

    events = [extract_event_data(event) for event in google_events if 'summary' in event]
    return events

@app.route('/event/<event_id>')
def event_specific(event_id):
    print(f'Received event_id: {event_id}')
    
    # Fetch event data based on event_id
    events = fetch_event_data(None, event_id=event_id)
    
    print(f'Fetched events: {events}')

    if events:
        event = events[0]  # Assume there's only one event with the given eventId
        return render_template('event_specific.html', event=event)
    else:
        return "Event not found"

>>>>>>> Stashed changes
@app.route('/', methods=['GET', 'POST'])
def event_list():
    if request.method == 'POST':
        time_range = request.form['time_range']
    else:
        time_range = 'month'  # Default to 'month'

    # Set time_max based on the selected time_range
    if time_range == 'week':
        time_max = (datetime.datetime.utcnow() + relativedelta(weeks=1)).isoformat() + 'Z'
    elif time_range == 'month':
        time_max = (datetime.datetime.utcnow() + relativedelta(months=1)).isoformat() + 'Z'
    elif time_range == 'year':
        time_max = (datetime.datetime.utcnow() + relativedelta(years=1)).isoformat() + 'Z'

    google_events = get_google_calendar_events(time_max)
    events = []

    for event in google_events:
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

        if start_date != end_date:
            event_data = {
                'name': event['summary'],
                'datetime': f"{start_day} {start_date} {start_time} -> {end_day} {end_date} {end_time}",
                'location': event.get('location', 'No location provided'),
            }
        elif start_date == end_date:
            event_data = {
                'name': event['summary'],
                'datetime': f"{start_day} {start_date} {start_time} -> {end_time}",
                'location': event.get('location', 'No location provided'),
            }
        events.append(event_data)

    return render_template('index.html', events=events, selected_time_range=time_range)

if __name__ == '__main__':
        app.run(debug=True)