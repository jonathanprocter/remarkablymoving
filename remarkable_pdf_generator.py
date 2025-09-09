#!/usr/bin/env python3
"""
reMarkable Pro Move Calendar PDF Generator
Optimized for reMarkable Pro Move (7.3" screen)
Dimensions: 1696×954 pixels
Physical size: 163mm × 91mm (landscape), 91mm × 163mm (portrait)
"""

import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import json
import sys

# reMarkable Pro Move specifications (7.3" screen)
# Physical dimensions in mm converted to points (1mm = 2.834645669 points)
REMARKABLE_MOVE_WIDTH_MM = 91  # Portrait width / Landscape height
REMARKABLE_MOVE_HEIGHT_MM = 163  # Portrait height / Landscape width

# Convert mm to points for ReportLab
REMARKABLE_MOVE_WIDTH_PT = REMARKABLE_MOVE_WIDTH_MM * mm
REMARKABLE_MOVE_HEIGHT_PT = REMARKABLE_MOVE_HEIGHT_MM * mm

# Define page sizes for reMarkable Pro Move
landscape_size = (REMARKABLE_MOVE_HEIGHT_PT, REMARKABLE_MOVE_WIDTH_PT)  # 163mm × 91mm
portrait_size = (REMARKABLE_MOVE_WIDTH_PT, REMARKABLE_MOVE_HEIGHT_PT)   # 91mm × 163mm

def create_weekly_view_with_events(c, week_start_date, events):
    """Create the landscape weekly overview page (Page 1)"""
    c.setPageSize(landscape_size)
    
    # Page background (white)
    c.setFillColor(colors.white)
    c.rect(0, 0, landscape_size[0], landscape_size[1], fill=1, stroke=0)
    
    # Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    title_text = f"WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}"
    c.drawCentredString(landscape_size[0]/2, landscape_size[1] - 7*mm, title_text)
    
    # Grid layout parameters
    margin_left = 8*mm
    margin_right = 8*mm
    margin_top = 12*mm
    margin_bottom = 8*mm
    
    grid_width = landscape_size[0] - margin_left - margin_right
    grid_height = landscape_size[1] - margin_top - margin_bottom
    
    # Column widths
    time_col_width = 15*mm
    day_col_width = (grid_width - time_col_width) / 7
    
    # Row heights
    header_height = 7*mm
    time_slots = 31  # 07:00 to 22:00 in 30-minute intervals
    row_height = (grid_height - header_height) / time_slots
    
    # Grid positioning
    grid_left = margin_left
    grid_right = margin_left + grid_width
    grid_top = landscape_size[1] - margin_top
    grid_bottom = margin_bottom
    
    # Draw outer border
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(grid_left, grid_bottom, grid_width, grid_height, fill=0, stroke=1)
    
    # Draw header background
    c.setFillColor(colors.Color(0.95, 0.95, 0.95))  # Light gray
    c.rect(grid_left + time_col_width, grid_top - header_height, 
           grid_width - time_col_width, header_height, fill=1, stroke=0)
    
    # Draw header separator line
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.75)
    c.line(grid_left, grid_top - header_height, grid_right, grid_top - header_height)
    
    # Draw vertical line after time column
    c.setLineWidth(0.75)
    c.line(grid_left + time_col_width, grid_bottom, 
           grid_left + time_col_width, grid_top)
    
    # Draw day column separators
    c.setLineWidth(0.5)
    for i in range(1, 7):
        x = grid_left + time_col_width + (i * day_col_width)
        c.line(x, grid_bottom, x, grid_top - header_height)
    
    # Draw day headers
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    for i, day in enumerate(days):
        x = grid_left + time_col_width + (i * day_col_width) + day_col_width/2
        y = grid_top - header_height/2 - 1*mm
        c.drawCentredString(x, y, day)
        
        # Add day numbers
        day_date = week_start_date + datetime.timedelta(days=i)
        c.setFont("Helvetica", 5)
        c.drawCentredString(x, y - 2.5*mm, str(day_date.day))
        c.setFont("Helvetica-Bold", 7)
    
    # Draw horizontal lines for time slots
    for i in range(1, time_slots):
        y = grid_top - header_height - (i * row_height)
        
        # Thicker lines for hours (even slots)
        if i % 2 == 0:
            c.setLineWidth(0.3)
            c.setStrokeColor(colors.Color(0.6, 0.6, 0.6))
        else:
            c.setLineWidth(0.2)
            c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
        
        c.line(grid_left, y, grid_right, y)
    
    # Draw time labels
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6)
    for i in range(time_slots):
        hour = 7 + (i // 2)
        minute = (i % 2) * 30
        time_str = f"{hour:02d}:{minute:02d}"
        
        x = grid_left + time_col_width/2
        y = grid_top - header_height - (i * row_height) - row_height/2
        c.drawCentredString(x, y, time_str)
    
    # Add events to weekly view
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
                # Calculate row positions
                start_slot = (start_hour - 7) * 2
                end_slot = (end_hour - 7) * 2
                
                # Calculate event position
                event_x = grid_left + time_col_width + (day_offset * day_col_width) + 1*mm
                event_y_top = grid_top - header_height - (start_slot * row_height)
                event_height = (end_slot - start_slot) * row_height - 0.5*mm
                event_width = day_col_width - 2*mm
                
                if event_height > 0:
                    # Draw event block with rounded corners effect
                    c.setFillColor(colors.lightblue)
                    c.setStrokeColor(colors.Color(0.4, 0.6, 0.8))
                    c.setLineWidth(0.5)
                    c.rect(event_x, event_y_top - event_height, 
                           event_width, event_height, fill=1, stroke=1)
                    
                    # Add event text
                    c.setFillColor(colors.black)
                    title = event.get('title', event.get('summary', 'Event'))
                    
                    # Truncate title to fit
                    c.setFont("Helvetica", 4)
                    max_chars = int(event_width / 1.3)
                    if len(title) > max_chars:
                        title = title[:max_chars-2] + ".."
                    
                    text_y = event_y_top - 2*mm
                    if text_y > event_y_top - event_height + 1*mm:
                        c.drawString(event_x + 0.5*mm, text_y, title)
                        
                    # Add time if space allows
                    if event_height > 5*mm:
                        c.setFont("Helvetica", 3)
                        time_text = f"{start_time.strftime('%H:%M')}"
                        c.drawString(event_x + 0.5*mm, text_y - 2*mm, time_text)
    
    c.showPage()

def create_daily_view_with_events(c, date, day_name, page_num, day_events):
    """Create portrait daily view pages (Pages 2-8)"""
    c.setPageSize(portrait_size)
    
    # Page background
    c.setFillColor(colors.white)
    c.rect(0, 0, portrait_size[0], portrait_size[1], fill=1, stroke=0)
    
    # Header
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(portrait_size[0]/2, portrait_size[1] - 8*mm, 
                       day_name.upper())
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(portrait_size[0]/2, portrait_size[1] - 12*mm,
                       date.strftime('%B %d, %Y'))
    
    # Back to weekly link
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.blue)
    c.drawString(6*mm, portrait_size[1] - 8*mm, "← Weekly")
    c.linkRect("", "weekly_view", 
              (5*mm, portrait_size[1] - 9*mm, 25*mm, portrait_size[1] - 6*mm))
    c.setFillColor(colors.black)
    
    # Grid layout parameters
    margin_left = 6*mm
    margin_right = 6*mm
    margin_top = 18*mm
    margin_bottom = 30*mm  # Space for notes
    
    grid_width = portrait_size[0] - margin_left - margin_right
    grid_height = portrait_size[1] - margin_top - margin_bottom
    
    # Column widths
    time_col_width = 14*mm
    event_col_width = grid_width - time_col_width
    
    # Time slots
    time_slots = 31  # 07:00 to 22:00
    row_height = grid_height / time_slots
    
    # Grid positioning
    grid_left = margin_left
    grid_right = margin_left + grid_width
    grid_top = portrait_size[1] - margin_top
    grid_bottom = margin_bottom
    
    # Draw main grid border
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(grid_left, grid_bottom, grid_width, grid_height, fill=0, stroke=1)
    
    # Draw time column separator
    c.setLineWidth(0.75)
    c.line(grid_left + time_col_width, grid_bottom, 
           grid_left + time_col_width, grid_top)
    
    # Shade time column slightly
    c.setFillColor(colors.Color(0.98, 0.98, 0.98))
    c.rect(grid_left, grid_bottom, time_col_width, grid_height, fill=1, stroke=0)
    
    # Draw horizontal lines for time slots
    for i in range(1, time_slots):
        y = grid_top - (i * row_height)
        
        # Different line styles for hours vs half-hours
        if i % 2 == 0:  # Hour lines
            c.setLineWidth(0.4)
            c.setStrokeColor(colors.Color(0.5, 0.5, 0.5))
        else:  # Half-hour lines
            c.setLineWidth(0.2)
            c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
        
        c.line(grid_left + time_col_width, y, grid_right, y)
    
    # Draw time labels
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6)
    for i in range(time_slots):
        hour = 7 + (i // 2)
        minute = (i % 2) * 30
        time_str = f"{hour:02d}:{minute:02d}"
        
        x = grid_left + time_col_width/2
        y = grid_top - (i * row_height) - row_height/2
        c.drawCentredString(x, y, time_str)
    
    # Add events to daily view
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
            # Calculate position
            start_slot = (start_hour - 7) * 2
            end_slot = (end_hour - 7) * 2
            
            event_x = grid_left + time_col_width + 1.5*mm
            event_y_top = grid_top - (start_slot * row_height)
            event_height = (end_slot - start_slot) * row_height - 1*mm
            event_width = event_col_width - 3*mm
            
            if event_height > 0:
                # Draw event block
                c.setFillColor(colors.lightblue)
                c.setStrokeColor(colors.Color(0.4, 0.6, 0.8))
                c.setLineWidth(0.5)
                c.rect(event_x, event_y_top - event_height, 
                       event_width, event_height, fill=1, stroke=1)
                
                # Add event text
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 6)
                title = event.get('title', event.get('summary', 'Event'))
                
                # Title
                text_y = event_y_top - 3*mm
                if text_y > event_y_top - event_height + 1*mm:
                    # Truncate if needed
                    max_width = event_width - 2*mm
                    if len(title) * 1.5 > max_width/mm:
                        title = title[:int(max_width/mm/1.5)-2] + ".."
                    c.drawString(event_x + 1*mm, text_y, title)
                    
                    # Time
                    if event_height > 6*mm:
                        c.setFont("Helvetica", 5)
                        time_text = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                        c.drawString(event_x + 1*mm, text_y - 3*mm, time_text)
                    
                    # Location/Description if space
                    if event_height > 10*mm:
                        location = event.get('location', '')
                        description = event.get('description', '')
                        extra_text = location or description
                        if extra_text:
                            c.setFont("Helvetica", 4)
                            extra_text = extra_text[:40]
                            if len(location or description) > 40:
                                extra_text += "..."
                            c.drawString(event_x + 1*mm, text_y - 6*mm, extra_text)
    
    # Notes section
    notes_y = grid_bottom - 5*mm
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin_left, notes_y, "NOTES")
    
    # Draw note lines
    c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
    c.setLineWidth(0.3)
    line_spacing = 4*mm
    notes_width = portrait_size[0] - margin_left - margin_right - 30*mm
    
    for i in range(4):
        y = notes_y - 5*mm - (i * line_spacing)
        c.line(margin_left, y, margin_left + notes_width, y)
    
    # Priority box
    priority_x = portrait_size[0] - margin_right - 28*mm
    priority_y = notes_y - 3*mm
    priority_width = 27*mm
    priority_height = 18*mm
    
    # Draw priority box
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(priority_x, priority_y - priority_height, priority_width, priority_height, fill=0, stroke=1)
    
    # Priority header
    c.setFont("Helvetica-Bold", 6)
    c.drawString(priority_x + 1*mm, priority_y - 2*mm, "TOP PRIORITIES")
    
    # Priority lines
    c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
    c.setLineWidth(0.2)
    for i in range(3):
        y = priority_y - 5*mm - (i * 4*mm)
        c.line(priority_x + 1*mm, y, priority_x + priority_width - 1*mm, y)
        # Add bullet points
        c.setFont("Helvetica", 5)
        c.drawString(priority_x + 1*mm, y + 0.5*mm, f"{i+1}.")
    
    c.showPage()

def generate_calendar_pdf(filename, week_start_date, events):
    """Generate the complete 8-page PDF with weekly and daily views"""
    c = canvas.Canvas(filename, pagesize=landscape_size)
    c.setAuthor("reMarkable Calendar Exporter")
    c.setTitle("Weekly Calendar - reMarkable Pro Move Optimized")
    
    # Set document metadata
    c.setPageSize(landscape_size)
    
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
        
        c.bookmarkPage(f"day_{i+1}")
        c.addOutlineEntry(day, f"day_{i+1}", 1, 0)
        create_daily_view_with_events(c, date, day, i + 2, day_events)
    
    c.save()
    print(f"✅ PDF generated successfully: {filename}")
    print(f"   Format: 8 pages (1 landscape weekly + 7 portrait daily)")
    print(f"   Dimensions: {REMARKABLE_MOVE_HEIGHT_MM}×{REMARKABLE_MOVE_WIDTH_MM}mm (landscape), {REMARKABLE_MOVE_WIDTH_MM}×{REMARKABLE_MOVE_HEIGHT_MM}mm (portrait)")
    print(f"   Optimized for: reMarkable Pro Move (7.3\" screen)")
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
            end_time = '17:00'  # Full day events span business hours
            duration = 480
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
            "title": "Team Standup",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "09:30",
            "description": "Daily sync"
        },
        {
            "title": "Design Review",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "10:00",
            "end_time": "11:30",
            "description": "Review new mockups",
            "location": "Conference Room A"
        },
        {
            "title": "Lunch Meeting",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "12:00",
            "end_time": "13:00",
            "location": "Cafe"
        },
        {
            "title": "Client Call",
            "date": (week_start_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:00",
            "description": "Quarterly review"
        },
        {
            "title": "Workshop",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "09:30",
            "end_time": "12:00",
            "description": "Team building workshop",
            "location": "Main Office"
        },
        {
            "title": "Sprint Planning",
            "date": (week_start_date + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            "start_time": "10:00",
            "end_time": "11:30",
            "description": "Plan next sprint"
        },
        {
            "title": "1:1 Meeting",
            "date": (week_start_date + datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
            "start_time": "15:00",
            "end_time": "16:00",
            "description": "Manager check-in"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_calendar_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()