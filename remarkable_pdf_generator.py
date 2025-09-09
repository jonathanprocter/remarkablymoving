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
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    title_y = landscape_size[1] - 8*mm
    c.drawCentredString(landscape_size[0]/2, title_y, 
                       f"WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}")
    
    # Define layout parameters
    margin = 5*mm
    grid_top = landscape_size[1] - 12*mm
    grid_bottom = 5*mm
    grid_height = grid_top - grid_bottom
    
    # Column setup (time column + 7 day columns)
    time_col_width = 12*mm
    day_col_width = (landscape_size[0] - 2*margin - time_col_width) / 7
    
    # Row setup (31 half-hour slots from 07:00 to 22:00)
    header_height = 6*mm
    time_slots = 31  # 07:00 to 22:00 in 30-minute intervals
    row_height = (grid_height - header_height) / time_slots
    
    # Days of the week header
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    c.setFont("Helvetica-Bold", 7)
    
    # Draw day headers
    for i, day in enumerate(days):
        x = margin + time_col_width + (i * day_col_width) + day_col_width/2
        y = grid_top - header_height/2
        c.drawCentredString(x, y, day)
    
    # Draw grid structure
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    # Draw outer border
    c.rect(margin, grid_bottom, landscape_size[0] - 2*margin, grid_height)
    
    # Draw header separator
    c.line(margin, grid_top - header_height, 
           landscape_size[0] - margin, grid_top - header_height)
    
    # Draw vertical lines
    # Time column separator
    c.line(margin + time_col_width, grid_bottom, 
           margin + time_col_width, grid_top)
    
    # Day column separators
    for i in range(1, 7):
        x = margin + time_col_width + (i * day_col_width)
        c.line(x, grid_bottom, x, grid_top - header_height)
    
    # Draw horizontal lines for time slots
    c.setLineWidth(0.25)
    for i in range(1, time_slots):
        y = grid_top - header_height - (i * row_height)
        # Full lines for hour marks
        if i % 2 == 0:
            c.setLineWidth(0.3)
        else:
            c.setLineWidth(0.2)
        c.line(margin, y, landscape_size[0] - margin, y)
    
    # Draw time labels
    c.setFont("Helvetica", 5)
    for i in range(time_slots):
        hour = 7 + (i // 2)
        minute = (i % 2) * 30
        time_str = f"{hour:02d}:{minute:02d}"
        
        x = margin + time_col_width/2
        y = grid_top - header_height - (i * row_height) - row_height/2
        c.drawCentredString(x, y, time_str)
    
    # Add events to weekly view
    c.setFont("Helvetica", 4)
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
                event_x = margin + time_col_width + (day_offset * day_col_width) + 1*mm
                event_y_top = grid_top - header_height - (start_slot * row_height)
                event_height = (end_slot - start_slot) * row_height
                
                if event_height > 0:
                    # Draw event block
                    c.setFillColor(colors.lightblue)  # Light blue
                    c.rect(event_x, event_y_top - event_height, 
                           day_col_width - 2*mm, event_height, fill=1, stroke=1)
                    
                    # Add event text
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica", 4)
                    title = event.get('title', event.get('summary', 'Event'))
                    # Truncate title to fit
                    max_chars = int(day_col_width / 1.2)
                    if len(title) > max_chars:
                        title = title[:max_chars-2] + ".."
                    
                    text_y = event_y_top - 2*mm
                    if text_y > event_y_top - event_height + 1*mm:
                        c.drawString(event_x + 0.5*mm, text_y, title)
    
    c.showPage()

def create_daily_view_with_events(c, date, day_name, page_num, day_events):
    """Create portrait daily view pages (Pages 2-8)"""
    c.setPageSize(portrait_size)
    
    # Header
    c.setFont("Helvetica-Bold", 10)
    header_y = portrait_size[1] - 8*mm
    c.drawCentredString(portrait_size[0]/2, header_y, 
                       f"{day_name.upper()}")
    
    c.setFont("Helvetica", 8)
    c.drawCentredString(portrait_size[0]/2, header_y - 4*mm,
                       f"{date.strftime('%B %d, %Y')}")
    
    # Back to weekly link
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.blue)
    c.drawString(5*mm, portrait_size[1] - 5*mm, "← Weekly")
    c.linkRect("", "weekly_view", 
              (5*mm, portrait_size[1] - 6*mm, 20*mm, portrait_size[1] - 3*mm))
    c.setFillColor(colors.black)
    
    # Grid layout parameters
    margin = 5*mm
    grid_top = portrait_size[1] - 15*mm
    grid_bottom = 25*mm  # Leave space for notes
    grid_height = grid_top - grid_bottom
    grid_width = portrait_size[0] - 2*margin
    
    # Time column width
    time_col_width = 12*mm
    event_col_width = grid_width - time_col_width
    
    # Time slots (31 half-hour slots)
    time_slots = 31
    row_height = grid_height / time_slots
    
    # Draw main grid border
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(margin, grid_bottom, grid_width, grid_height)
    
    # Draw time column separator
    c.line(margin + time_col_width, grid_bottom, 
           margin + time_col_width, grid_top)
    
    # Draw horizontal lines for time slots
    for i in range(1, time_slots):
        y = grid_top - (i * row_height)
        # Thicker lines for hours
        if i % 2 == 0:
            c.setLineWidth(0.3)
            c.setStrokeColor(colors.gray)
        else:
            c.setLineWidth(0.2)
            c.setStrokeColor(colors.lightgrey)
        c.line(margin + time_col_width, y, margin + grid_width, y)
    
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    # Draw time labels
    c.setFont("Helvetica", 6)
    for i in range(time_slots):
        hour = 7 + (i // 2)
        minute = (i % 2) * 30
        time_str = f"{hour:02d}:{minute:02d}"
        
        x = margin + time_col_width/2
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
            
            event_x = margin + time_col_width + 1*mm
            event_y_top = grid_top - (start_slot * row_height)
            event_height = (end_slot - start_slot) * row_height
            
            if event_height > 0:
                # Draw event block
                c.setFillColor(colors.Color(0.85, 0.95, 1.0))  # Light blue
                c.rect(event_x, event_y_top - event_height, 
                       event_col_width - 2*mm, event_height, fill=1, stroke=1)
                
                # Add event text
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 6)
                title = event.get('title', event.get('summary', 'Event'))
                
                # Calculate available space for text
                text_lines = []
                text_y = event_y_top - 3*mm
                
                # Title
                if text_y > event_y_top - event_height + 2*mm:
                    max_width = event_col_width - 4*mm
                    if len(title) * 1.8 > max_width/mm:
                        title = title[:int(max_width/mm/1.8)-2] + ".."
                    c.drawString(event_x + 1*mm, text_y, title)
                    
                    # Time
                    c.setFont("Helvetica", 5)
                    time_text = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    if text_y - 3*mm > event_y_top - event_height + 1*mm:
                        c.drawString(event_x + 1*mm, text_y - 3*mm, time_text)
                    
                    # Description if space allows
                    description = event.get('description', event.get('location', ''))
                    if description and text_y - 6*mm > event_y_top - event_height + 1*mm:
                        c.setFont("Helvetica", 4)
                        desc_text = description[:40]
                        if len(description) > 40:
                            desc_text += "..."
                        c.drawString(event_x + 1*mm, text_y - 6*mm, desc_text)
    
    # Notes section at bottom
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, grid_bottom - 5*mm, "NOTES:")
    
    # Draw note lines
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.3)
    line_spacing = 4*mm
    for i in range(3):
        y = grid_bottom - 8*mm - (i * line_spacing)
        c.line(margin, y, portrait_size[0] - margin, y)
    
    # Priority/Goals section (small box on right)
    priority_x = portrait_size[0] - margin - 25*mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(priority_x, grid_bottom - 20*mm, 25*mm, 15*mm)
    c.setFont("Helvetica", 5)
    c.drawString(priority_x + 1*mm, grid_bottom - 7*mm, "Priorities:")
    
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
    
    # Sample events
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
            "description": "Team lunch"
        },
        {
            "title": "Project Review",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:30",
            "description": "Quarterly project review"
        },
        {
            "title": "Client Call",
            "date": (week_start_date + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            "start_time": "10:00",
            "end_time": "11:00",
            "description": "Monthly sync with client"
        },
        {
            "title": "Planning Session",
            "date": (week_start_date + datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
            "start_time": "09:30",
            "end_time": "11:30",
            "description": "Sprint planning"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_move_calendar_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()