#!/usr/bin/env python3
"""
reMarkable Pro Move Calendar PDF Generator
Optimized for reMarkable Paper Pro Move (7.3" screen - 1696x954 resolution)
Dimensions: 91mm × 163mm portrait, 163mm × 91mm landscape
"""

import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
import json
import sys

# reMarkable Paper Pro Move specifications (7.3" screen)
# Resolution: 1696 × 954 pixels
# Physical dimensions in mm converted to points (1mm = 2.834645669 points)
REMARKABLE_MOVE_WIDTH_MM = 91  # mm
REMARKABLE_MOVE_HEIGHT_MM = 163  # mm

# Convert mm to points for ReportLab
MM_TO_POINTS = 2.834645669
REMARKABLE_MOVE_WIDTH = REMARKABLE_MOVE_WIDTH_MM * MM_TO_POINTS  # 258 points
REMARKABLE_MOVE_HEIGHT = REMARKABLE_MOVE_HEIGHT_MM * MM_TO_POINTS  # 462 points

# Define page sizes for reMarkable Pro Move
landscape_size = (REMARKABLE_MOVE_HEIGHT, REMARKABLE_MOVE_WIDTH)  # 163mm x 91mm
portrait_size = (REMARKABLE_MOVE_WIDTH, REMARKABLE_MOVE_HEIGHT)   # 91mm x 163mm

def create_weekly_view_with_events(c, week_start_date, events):
    """Create the landscape weekly overview page (Page 1)"""
    c.setPageSize(landscape_size)
    
    # Smaller font sizes for 7.3" screen
    c.setFont("Helvetica-Bold", 14)
    margin = 10
    c.drawString(margin, landscape_size[1] - margin - 10, 
                f"WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}")
    
    # Draw weekly grid
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    x_start = margin
    y_start = landscape_size[1] - 35
    col_width = (landscape_size[0] - 2 * margin) / 8  # Time column + 7 days
    
    # Calculate row height for 31 time slots (07:00-22:00 with 30-min intervals)
    available_height = landscape_size[1] - 45
    row_height = available_height / 32  # 31 time slots + header
    
    # Draw day headers with clickable links
    c.setFont("Helvetica-Bold", 8)
    for i, day in enumerate(days):
        x_pos = x_start + (i + 1) * col_width + 2
        y_pos = y_start
        # Abbreviated day names for space
        day_abbr = day[:3]
        c.drawString(x_pos, y_pos, day_abbr)
        # Add clickable links to daily pages (pages 2-8)
        link_rect = (x_start + (i + 1) * col_width, y_pos - 2, 
                    x_start + (i + 2) * col_width, y_pos + row_height)
        # Link to page 2 for Monday, page 3 for Tuesday, etc.
        c.linkAbsolute(f"", f"day_{i+1}", link_rect, Border='[0 0 0]')
    
    # Draw time slots (07:00-22:00 in military time with 30-minute intervals)
    c.setFont("Helvetica", 6)
    time_y = y_start - row_height
    for hour in range(7, 23):  # 7 AM to 10 PM
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            c.drawString(x_start + 2, time_y, time_str)
            time_y -= row_height
            if hour == 22 and minute == 0:  # Stop at 22:00
                break
    
    # Draw grid lines
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.5)
    
    # Vertical lines
    for i in range(9):  # Time column + 7 day columns + right border
        x_pos = x_start + i * col_width
        c.line(x_pos, y_start + row_height, x_pos, y_start - 31 * row_height)
    
    # Horizontal lines
    for i in range(33):  # Header + 31 time slots + bottom
        y_pos = y_start + row_height - i * row_height
        c.line(x_start, y_pos, x_start + 8 * col_width, y_pos)
    
    # Add events to weekly view with proportional blocks
    c.setFont("Helvetica", 5)
    for event in events:
        event_date_str = event.get('date')
        if not event_date_str:
            continue
            
        try:
            event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue
            
        day_offset = (event_date - week_start_date).days
        
        if 0 <= day_offset < 7:
            start_time_str = event.get('start_time', event.get('time', '09:00'))
            end_time_str = event.get('end_time', '')
            
            try:
                start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            except (ValueError, TypeError):
                start_time = datetime.time(9, 0)
            
            if not end_time_str:
                duration = event.get('duration', 60)
                end_hour = start_time.hour + (start_time.minute + duration) // 60
                end_minute = (start_time.minute + duration) % 60
                end_time = datetime.time(min(end_hour, 22), end_minute)
            else:
                try:
                    end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
                except (ValueError, TypeError):
                    end_time = datetime.time(start_time.hour + 1, start_time.minute)
            
            # Calculate position
            start_hour = start_time.hour + start_time.minute / 60
            end_hour = end_time.hour + end_time.minute / 60
            
            if 7 <= start_hour <= 22:
                # Calculate row position (each half hour is one row)
                start_row = (start_hour - 7) * 2
                end_row = min((end_hour - 7) * 2, 31)
                
                event_x = x_start + (day_offset + 1) * col_width + 1
                event_y_start = y_start - start_row * row_height
                event_height = max((end_row - start_row) * row_height, row_height * 0.8)
                
                # Draw event block
                c.setFillColor(colors.lightblue)
                c.rect(event_x, event_y_start - event_height, col_width - 2, event_height, fill=1)
                
                # Add event text (truncated for small space)
                c.setFillColor(colors.black)
                title = event.get('title', event.get('summary', 'Event'))[:10]
                c.drawString(event_x + 1, event_y_start - 6, title)
    
    c.showPage()

def create_daily_view_with_events(c, date, day_name, page_num, day_events):
    """Create portrait daily view pages (Pages 2-8)"""
    c.setPageSize(portrait_size)
    
    # Add bookmark for this day
    c.bookmarkPage(f"day_{page_num-1}")
    
    # Smaller fonts for 7.3" screen
    c.setFont("Helvetica-Bold", 12)
    margin = 10
    c.drawString(margin, portrait_size[1] - margin - 10, 
                f"{day_name.upper()} - {date.strftime('%B %d, %Y')}")
    
    # Add link back to weekly view
    c.setFont("Helvetica", 8)
    back_text = "← Week"
    c.drawString(margin, portrait_size[1] - margin - 22, back_text)
    # Link back to page 1 (weekly view)
    c.linkAbsolute("", "weekly_view", 
                  (margin, portrait_size[1] - margin - 25, margin + 40, portrait_size[1] - margin - 15),
                  Border='[0 0 0]')
    
    # Draw daily schedule
    x_start = margin
    y_start = portrait_size[1] - 40
    time_col_width = 30
    
    # Calculate row height for time slots
    available_height = portrait_size[1] - 50
    row_height = available_height / 31  # 31 half-hour slots
    
    # Draw time slots (07:00-22:00 in military time with 30-minute intervals)
    c.setFont("Helvetica", 7)
    time_y = y_start
    for hour in range(7, 23):  # 7 AM to 10 PM
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            c.drawString(x_start + 2, time_y, time_str)
            time_y -= row_height
            if hour == 22 and minute == 0:  # Stop at 22:00
                break
    
    # Draw grid lines
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.5)
    
    # Vertical line separating time from events
    c.line(x_start + time_col_width, y_start + row_height, 
           x_start + time_col_width, y_start - 30 * row_height)
    
    # Horizontal lines for each time slot
    for i in range(32):  # 31 time slots + top border
        y_pos = y_start + row_height - i * row_height
        c.line(x_start, y_pos, portrait_size[0] - margin, y_pos)
    
    # Add events to daily view
    c.setFont("Helvetica", 7)
    for event in day_events:
        start_time_str = event.get('start_time', event.get('time', '09:00'))
        end_time_str = event.get('end_time', '')
        
        try:
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            start_time = datetime.time(9, 0)
        
        if not end_time_str:
            duration = event.get('duration', 60)
            end_hour = start_time.hour + (start_time.minute + duration) // 60
            end_minute = (start_time.minute + duration) % 60
            end_time = datetime.time(min(end_hour, 22), end_minute)
        else:
            try:
                end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
            except (ValueError, TypeError):
                end_time = datetime.time(start_time.hour + 1, start_time.minute)
        
        start_hour = start_time.hour + start_time.minute / 60
        end_hour = end_time.hour + end_time.minute / 60
        
        if 7 <= start_hour <= 22:
            start_row = (start_hour - 7) * 2
            end_row = min((end_hour - 7) * 2, 31)
            
            event_x = x_start + time_col_width + 2
            event_y_start = y_start - start_row * row_height
            event_height = max((end_row - start_row) * row_height, row_height * 0.8)
            event_width = portrait_size[0] - event_x - margin - 2
            
            # Draw event block
            c.setFillColor(colors.lightblue)
            c.rect(event_x, event_y_start - event_height, event_width, event_height, fill=1)
            
            # Add event text
            c.setFillColor(colors.black)
            title = event.get('title', event.get('summary', 'Untitled'))
            # Truncate title if too long
            if len(title) > 30:
                title = title[:27] + "..."
            c.drawString(event_x + 2, event_y_start - 8, title)
            
            # Add description if space allows and exists
            description = event.get('description', event.get('location', ''))
            if description and event_height > row_height * 1.5:
                c.setFont("Helvetica", 6)
                if len(description) > 40:
                    description = description[:37] + "..."
                c.drawString(event_x + 2, event_y_start - 14, description)
                c.setFont("Helvetica", 7)
    
    c.showPage()

def generate_calendar_pdf(filename, week_start_date, events):
    """Generate the complete PDF with exactly 8 pages"""
    c = canvas.Canvas(filename)
    c.setAuthor("reMarkable Calendar Exporter")
    c.setTitle("Weekly Calendar - reMarkable Paper Pro Move Optimized")
    
    # Page 1: Weekly overview (landscape)
    c.bookmarkPage("weekly_view")
    c.addOutlineEntry("Weekly Overview", "weekly_view", 0, 0)
    create_weekly_view_with_events(c, week_start_date, events)
    
    # Pages 2-8: Daily views (portrait) - Monday through Sunday
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, day in enumerate(days):
        date = week_start_date + datetime.timedelta(days=i)
        
        # Filter events for this specific day
        day_events = []
        for event in events:
            event_date_str = event.get('date')
            if event_date_str:
                try:
                    event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                    if event_date == date:
                        day_events.append(event)
                except (ValueError, TypeError):
                    continue
        
        # Create bookmark and add to outline
        bookmark_name = f"day_{i+1}"
        c.addOutlineEntry(day, bookmark_name, 1, 0)
        
        # Create the daily page (page numbers 2-8)
        create_daily_view_with_events(c, date, day, i + 2, day_events)
    
    c.save()
    print(f"✅ PDF generated successfully: {filename}")
    print(f"   - 8 pages total (1 weekly + 7 daily)")
    print(f"   - Optimized for reMarkable Paper Pro Move (7.3\" screen)")
    print(f"   - Time range: 07:00-22:00 (military time with 30-min intervals)")
    return filename

def transform_google_calendar_events(google_events):
    """Transform Google Calendar events to the format expected by the PDF generator"""
    transformed_events = []
    
    for event in google_events:
        # Handle all-day events and regular events
        if 'dateTime' in event.get('start', {}):
            start_dt = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            date_str = start_dt.strftime('%Y-%m-%d')
            start_time = start_dt.strftime('%H:%M')
            end_time = end_dt.strftime('%H:%M')
            duration = int((end_dt - start_dt).total_seconds() / 60)
        elif 'date' in event.get('start', {}):
            # All-day event
            date_str = event['start']['date']
            start_time = '09:00'
            end_time = '10:00'
            duration = 60
        else:
            continue
        
        transformed_event = {
            'title': event.get('summary', 'Untitled Event'),
            'date': date_str,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'type': 'appointment'
        }
        
        transformed_events.append(transformed_event)
    
    return transformed_events

def generate_pdf_from_week_data(week_data, start_date, output_filename=None):
    """Generate PDF from week data (compatible with existing API)"""
    # Parse start date
    if isinstance(start_date, str):
        week_start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        week_start = start_date
    
    # Extract and transform events
    all_events = []
    
    # Handle events in the format from the JavaScript generator
    if 'events' in week_data:
        for day_key, day_events in week_data['events'].items():
            # Calculate the date for this day
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            if day_key.lower() in day_map:
                day_offset = day_map[day_key.lower()]
                event_date = week_start + datetime.timedelta(days=day_offset)
                
                for event in day_events:
                    transformed_event = {
                        'title': event.get('title', 'Untitled'),
                        'date': event_date.strftime('%Y-%m-%d'),
                        'start_time': event.get('time', '09:00'),
                        'duration': event.get('duration', 60),
                        'description': event.get('description', ''),
                        'type': event.get('type', 'appointment')
                    }
                    
                    # Calculate end time from duration
                    start_time = datetime.datetime.strptime(transformed_event['start_time'], '%H:%M').time()
                    end_hour = start_time.hour + (start_time.minute + transformed_event['duration']) // 60
                    end_minute = (start_time.minute + transformed_event['duration']) % 60
                    transformed_event['end_time'] = f"{end_hour:02d}:{end_minute:02d}"
                    
                    all_events.append(transformed_event)
    
    # Generate output filename if not provided
    if not output_filename:
        output_filename = f"remarkable_move_calendar_{week_start.strftime('%Y%m%d')}.pdf"
    
    # Generate the PDF
    generate_calendar_pdf(output_filename, week_start, all_events)
    
    return output_filename

def main():
    """Main function to generate calendar PDF"""
    # Get current week's Monday as default
    today = datetime.date.today()
    week_start_date = today - datetime.timedelta(days=today.weekday())
    
    # Sample events for testing
    events = [
        {
            "title": "Team Meeting",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:30",
            "description": "Weekly team sync"
        },
        {
            "title": "Lunch Break",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "12:00",
            "end_time": "13:00",
            "description": "Lunch"
        },
        {
            "title": "Project Review",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:30",
            "description": "Quarterly project review"
        },
        {
            "title": "Evening Workout",
            "date": (week_start_date + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            "start_time": "18:00",
            "end_time": "19:00",
            "description": "Gym session"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_move_calendar_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()