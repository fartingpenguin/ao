from flask import Flask, render_template, request
import datetime
from dateutil.relativedelta import relativedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os
import googlemaps
import urllib.parse

event_id = 'your_event_id'
encoded_event_id = urllib.parse.quote(event_id)
url = f'/event/{encoded_event_id}'


app = Flask(__name__)

# Load environment variables
load_dotenv()

# Define API scopes and global variables
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
gmaps = googlemaps.Client(key=os.getenv('api_key'))

# Function to fetch Google Calendar events
def get_google_calendar_events(time_range):
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
        time_max = None

        if time_range == 'week':
            time_max = (datetime.datetime.utcnow() + relativedelta(weeks=1)).isoformat() + 'Z'
        elif time_range == 'month':
            time_max = (datetime.datetime.utcnow() + relativedelta(months=1)).isoformat() + 'Z'
        elif time_range == 'year':
            time_max = (datetime.datetime.utcnow() + relativedelta(years=1)).isoformat() + 'Z'

        print(f'Getting the upcoming events for the next {time_range}')
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events
    except HttpError as error:
        print('An error occurred: %s' % error)
        return []

# Function to extract event data
def extract_event_data(event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))

    # Convert the date and time format to a more readable format
    start_datetime = datetime.datetime.fromisoformat(start)
    end_datetime = datetime.datetime.fromisoformat(end)

    home = '15 evelyn road'

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


def fetch_event_data(time_range, event_id=None):
    google_events = get_google_calendar_events(time_range)
    
    events = []

    for event in google_events:
        if 'summary' in event:
            event_data = {
                'eventId': event['id'],
                'name': event['summary'],
                'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date', '')),
                'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date', '')),
                'location': event.get('location', 'No location provided'),
                'datetime': '',  # Initialize datetime field
            }

            # Extract the date and time if available
            if event_data['start']:
                start_datetime = datetime.datetime.fromisoformat(event_data['start'])
                end_datetime = datetime.datetime.fromisoformat(event_data['end'])
                event_data['datetime'] = f"{start_datetime.strftime('%A, %d %B %Y %I:%M %p')} - {end_datetime.strftime('%I:%M %p')}"
            
            events.append(event_data)

    if event_id is not None:
        # If event_id is provided, filter the list to get only the specified event
        events = [event for event in events if event['eventId'] == event_id]

    return events
        

@app.route('/', methods=['GET', 'POST'])
def event_list():
    if request.method == 'POST':
        time_range = request.form['time_range']
    else:
        time_range = 'month'  # Default to 'month'

    events = fetch_event_data(time_range)
    return render_template('index.html', events=events, selected_time_range=time_range)

# Function to calculate distance for a specific mode
def distance(start_location, location, mode):
    result = gmaps.distance_matrix(start_location, location, mode)
    # Check if the result contains distance information
    if 'rows' in result and result['rows'][0]['elements'][0].get('distance'):
        return result['rows'][0]['elements'][0]['distance']['text']
    else:
        return 'Distance not available'

def time_taken(start_location, location, mode, start_time):
    distance_result = gmaps.distance_matrix(start_location, location, mode)

    # Get duration from result
    for row in distance_result['rows']:
        for element in row['elements']:
            duration_text = element['duration']['text']
            
            # Calculate departure time based on the event's start time
            duration = parse_duration(duration_text)
            departure_time = start_time - duration
            
            return duration_text, departure_time.strftime('%A, %d %B %Y %I:%M %p')

def parse_duration(duration_text):
    # Parse the duration text (e.g., "1 hour 30 mins") into a timedelta object
    parts = duration_text.split()
    duration = datetime.timedelta()

    for i in range(0, len(parts), 2):
        value = int(parts[i])
        unit = parts[i + 1]

        if 'hour' in unit:
            duration += datetime.timedelta(hours=value)
        elif 'min' in unit:
            duration += datetime.timedelta(minutes=value)

    return duration

# Function to calculate departure time based on mode
def calculate_departure_time(start_location, location, mode, start_time):
    distance_result = gmaps.distance_matrix(start_location, location, mode)

    # Get duration from result
    for row in distance_result['rows']:
        for element in row['elements']:
            duration_text = element['duration']['text']
            
            # Calculate departure time based on the event's start time
            duration = parse_duration(duration_text)
            departure_time = start_time - duration
            
            return departure_time.strftime('%A, %d %B %Y %I:%M %p')
# Define a function to parse the distance value from the distance text
def parse_distance(distance_text):
    try:
        # Assuming the distance text is in the format 'X.XX km' or 'X.XX mi'
        distance_parts = distance_text.split(' ')
        if len(distance_parts) == 2:
            return float(distance_parts[0])  # Extract the numeric part as a float
    except ValueError:
        pass
    return 0.0  # Return a default value if parsing fails

# Define a function to calculate the driving price based on distance
# Define a function to calculate the driving price based on distance
def calculate_driving_price(distance_value):
    # Implement your pricing logic here based on the distance traveled
    # For example, you can calculate the price per kilometer/mile and multiply by the distance
    price_per_km = 1.25  # Replace with your actual price per kilometer
    total_price = price_per_km * distance_value
    return round(total_price, 2)  # Round the total price to 2 decimal places

# Define a function to calculate the transit price based on distance
def calculate_transit_price(distance_value):
    # Implement your pricing logic for transit here based on the distance traveled
    # For example, you can calculate the price per kilometer/mile and multiply by the distance
    price_per_km = 0.10  # Replace with your actual price per kilometer for transit
    total_price = price_per_km * distance_value
    return round(total_price, 2)  # Round the total price to 2 decimal places
# Function to calculate carbon emissions for driving based on distance
def calculate_driving_emissions(distance_value):
    # Emission factor for an average car (g CO2 per km)
    emission_factor = 120  # Replace with the actual emission factor

    # Calculate emissions (g CO2)
    emissions = emission_factor * distance_value
    return round(emissions, 2)  # Round emissions to 2 decimal places

# Function to calculate carbon emissions for transit based on distance
def calculate_transit_emissions(distance_value):
    # Emission factor for public transit (g CO2 per km)
    emission_factor = 40  # Replace with the actual emission factor

    # Calculate emissions (g CO2)
    emissions = emission_factor * distance_value
    return round(emissions, 2)  # Round emissions to 2 decimal places



@app.route('/event/<event_id>', methods=['GET', 'POST'])
def event_specific(event_id):
    print(f'Received event_id: {event_id}')
    
    # Initialize custom start address to a default value
    custom_start_address = '15 evelyn road'

    if request.method == 'POST':
        # Get the custom start address from the form
        custom_start_address = request.form.get('start_address', custom_start_address)
    
    # Fetch event data based on event_id
    events = fetch_event_data(None, event_id=event_id)
    
    print(f'Fetched events: {events}')

    if events:
        event = events[0]  # Assume there's only one event with the given eventId

        # Format the start and end datetime strings
        start_datetime = event['start']
        end_datetime = event['end']

        if 'T' in start_datetime and 'T' in end_datetime:
            start_datetime = datetime.datetime.fromisoformat(start_datetime)
            end_datetime = datetime.datetime.fromisoformat(end_datetime)
            event['start'] = start_datetime.strftime('%A, %d %B %Y %I:%M %p')
            event['end'] = end_datetime.strftime('%A, %d %B %Y %I:%M %p')

        # Check if a location is provided for the event
        if 'location' in event:
            location = event['location']
        else:
            location = "No location provided"
            event['location'] = "No location provided"
        
        # Calculate distance and time taken if a location is provided
        modes = ['driving', 'transit', 'bicycling', 'walking']
        mode_data = {}
        display_price = ''

        # Get the selected time offset from the form
        selected_time_offset = int(request.form.get('time_offset', 0))
        for mode in modes:
            mode_data[mode] = {}
            try:
                mode_data[mode]['distance'] = distance(custom_start_address, location, mode)
                mode_data[mode]['time_taken'], mode_data[mode]['departure_time'] = time_taken(custom_start_address, location, mode, start_datetime)
                
                # Fetch and store the actual pricing data based on distance for driving and transit here
                if mode == 'driving':
                    # Calculate the price based on the distance (replace with your pricing logic)
                    distance_value = parse_distance(mode_data[mode]['distance'])  # Implement a function to parse distance
                    mode_data[mode]['price'] = calculate_driving_price(distance_value)  # Implement your pricing logic
                    display_price = 'Uber Price: '

                elif mode == 'transit':
                    # Calculate the price based on the distance (replace with your pricing logic)
                    distance_value = parse_distance(mode_data[mode]['distance'])  # Implement a function to parse distance
                    mode_data[mode]['price'] = calculate_transit_price(distance_value)  # Implement your pricing logic
                    display_price = 'Estimated Price: '
            except:
                mode_data[mode]['distance'] = 'Distance not available'
                mode_data[mode]['time_taken'] = f"Time by {mode}: Not available"
                mode_data[mode]['departure_time'] = f"Departure time by {mode}: Not available"
                mode_data[mode]['price'] = 'Price not available'
        mode_emissions = {}

        for mode in modes:
            mode_data[mode] = {}
            try:
                mode_data[mode]['distance'] = distance(custom_start_address, location, mode)
                mode_data[mode]['time_taken'], mode_data[mode]['departure_time'] = time_taken(custom_start_address, location, mode, start_datetime)

                # Calculate carbon emissions based on the distance
                if mode == 'driving':
                    distance_value = parse_distance(mode_data[mode]['distance'])
                    mode_data[mode]['emissions'] = calculate_driving_emissions(distance_value)
                elif mode == 'transit':
                    distance_value = parse_distance(mode_data[mode]['distance'])
                    mode_data[mode]['emissions'] = calculate_transit_emissions(distance_value)
            except:
                mode_data[mode]['distance'] = 'Distance not available'
                mode_data[mode]['time_taken'] = f"Time by {mode}: Not available"
                mode_data[mode]['departure_time'] = f"Departure time by {mode}: Not available"
                mode_data[mode]['emissions'] = 'Emissions not available'



        return render_template('event_specific.html', event=event, mode_data=mode_data, custom_start_address=custom_start_address, selected_time_offset=selected_time_offset, display_price=display_price)
    else:
        return "Event not found"
    
if __name__ == '__main__':
    app.run(debug=True)
