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

def format_time_military(hour, minute):
    """Format time in military format with leading zeros"""
    return f"{hour:02d}{minute:02d}"

def create_weekly_view_with_events(c, week_start_date, events):
    """Create the landscape weekly overview page (Page 1)"""
    c.setPageSize(landscape_size)
    
    # Smaller font sizes for 7.3" screen
    c.setFont("Helvetica-Bold", 14)
    c.drawString(10*mm, landscape_size[1] - 10*mm, 
                f"WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}")
    
    # Draw weekly grid
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    x_start = 8*mm
    y_start = landscape_size[1] - 15*mm
    col_width = (landscape_size[0] - 16*mm) / 8  # 8 columns: time + 7 days
    row_height = (landscape_size[1] - 20*mm) / 31  # 31 half-hour slots
    
    # Draw header with days (smaller font for Pro Move)
    c.setFont("Helvetica-Bold", 8)
    for i, day in enumerate(days):
        x_pos = x_start + (i + 1) * col_width + 2*mm
        c.drawString(x_pos, y_start + 1*mm, day[:3])  # Abbreviated day names
        # Add clickable links to daily pages
        link_rect = (x_start + (i + 1) * col_width, y_start - row_height, 
                    x_start + (i + 2) * col_width, y_start + row_height)
        c.linkRect(day, f"day_{i+1}", link_rect)
    
    # Draw time slots (0700-2200 hrs with :30 intervals)
    c.setFont("Helvetica", 6)
    for i in range(31):  # 31 half-hour slots from 07:00 to 22:00
        hour = (i // 2) + 7
        minute = 30 * (i % 2)
        time_str = format_time_military(hour, minute)
        c.drawString(x_start + 1*mm, y_start - (i + 1) * row_height + row_height/3, time_str)
    
    # Draw grid lines
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    # Vertical lines
    for i in range(9):  # 8 columns plus left border
        c.line(x_start + i * col_width, y_start + row_height, 
               x_start + i * col_width, y_start - 30 * row_height)
    
    # Horizontal lines
    for i in range(32):  # 31 time slots plus header
        c.line(x_start, y_start - (i-1) * row_height, 
               x_start + 8 * col_width, y_start - (i-1) * row_height)
    
    # Add events to weekly view (smaller text for Pro Move)
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
                start_row = (start_hour - 7) * 2
                end_row = (end_hour - 7) * 2
                
                event_x = x_start + (day_offset + 1) * col_width + 1*mm
                event_y_start = y_start - start_row * row_height
                event_height = max((end_row - start_row) * row_height, row_height / 2)
                
                # Draw event block
                c.setFillColor(colors.lightblue)
                c.rect(event_x, event_y_start - event_height, 
                       col_width - 2*mm, event_height, fill=1)
                
                # Add event text (truncated for small space)
                c.setFillColor(colors.black)
                title = event.get('title', event.get('summary', 'Untitled'))[:12]
                c.drawString(event_x + 1*mm, event_y_start - 3*mm, title)
    
    c.showPage()

def create_daily_view_with_events(c, date, day_name, page_num, day_events):
    """Create portrait daily view pages (Pages 2-8)"""
    c.setPageSize(portrait_size)
    
    # Header with day and date (smaller font for Pro Move)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(8*mm, portrait_size[1] - 10*mm, 
                f"{day_name.upper()} - {date.strftime('%B %d, %Y')}")
    
    # Add link back to weekly view
    c.setFont("Helvetica", 8)
    c.drawString(8*mm, portrait_size[1] - 15*mm, "← Back to Weekly")
    c.linkRect("← Back", "weekly_view", 
              (8*mm, portrait_size[1] - 17*mm, 30*mm, portrait_size[1] - 13*mm))
    
    # Draw daily schedule
    x_start = 8*mm
    y_start = portrait_size[1] - 20*mm
    time_col_width = 15*mm
    event_col_width = portrait_size[0] - x_start - time_col_width - 8*mm
    row_height = (portrait_size[1] - 30*mm) / 31  # 31 half-hour slots
    
    # Draw time slots (0700-2200 hrs with :30 intervals)
    c.setFont("Helvetica", 7)
    for i in range(31):  # 31 half-hour slots
        hour = (i // 2) + 7
        minute = 30 * (i % 2)
        time_str = format_time_military(hour, minute)
        c.drawString(x_start + 2*mm, y_start - i * row_height - row_height/2, time_str)
    
    # Draw grid lines
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    # Vertical line separating time from events
    c.line(x_start + time_col_width, y_start + row_height, 
           x_start + time_col_width, y_start - 30 * row_height)
    
    # Right border
    c.line(portrait_size[0] - 8*mm, y_start + row_height,
           portrait_size[0] - 8*mm, y_start - 30 * row_height)
    
    # Horizontal lines for each time slot
    for i in range(32):
        c.line(x_start, y_start - (i-1) * row_height, 
               portrait_size[0] - 8*mm, y_start - (i-1) * row_height)
    
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
            end_row = (end_hour - 7) * 2
            
            event_x = x_start + time_col_width + 2*mm
            event_y_start = y_start - start_row * row_height
            event_height = max((end_row - start_row) * row_height, row_height)
            
            # Draw event block
            c.setFillColor(colors.lightblue)
            c.rect(event_x, event_y_start - event_height, 
                   event_col_width - 4*mm, event_height, fill=1)
            
            # Add event text
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 7)
            title = event.get('title', event.get('summary', 'Untitled'))
            # Truncate long titles
            if len(title) > 25:
                title = title[:22] + "..."
            c.drawString(event_x + 2*mm, event_y_start - 4*mm, title)
            
            # Add description if available
            description = event.get('description', event.get('location', ''))
            if description:
                c.setFont("Helvetica", 6)
                desc_text = description[:35]
                if len(description) > 35:
                    desc_text += "..."
                c.drawString(event_x + 2*mm, event_y_start - 7*mm, desc_text)
    
    # Add space for notes at bottom
    c.setFont("Helvetica", 7)
    c.drawString(x_start, 15*mm, "Notes:")
    c.line(x_start, 13*mm, portrait_size[0] - 8*mm, 13*mm)
    c.line(x_start, 10*mm, portrait_size[0] - 8*mm, 10*mm)
    c.line(x_start, 7*mm, portrait_size[0] - 8*mm, 7*mm)
    
    c.showPage()

def generate_calendar_pdf(filename, week_start_date, events):
    """Generate the complete 8-page PDF with weekly and daily views"""
    c = canvas.Canvas(filename, pagesize=landscape_size)
    c.setAuthor("reMarkable Calendar Exporter")
    c.setTitle("Weekly Calendar - reMarkable Pro Move Optimized")
    
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
            "title": "Project Review",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:30",
            "description": "Quarterly project review"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_move_calendar_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()